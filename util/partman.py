"""
Clonix: util/partman.py

Partition manager
"""

import os
import re
from dataclasses import dataclass
from typing import Optional, Union, Dict

from loguru import logger

from util import get_drive_size_raw, get_physical_drives, run_subprocess

class Partman_Tui:
    pass # TODO

@dataclass
class Partition:
    index: int
    fstype: str
    mountpoint: str
    
    # RAW values (i.e. number of bytes)
    start: int
    size: int
    end: int


class Disk:
    size: int
    partitions: list

    def __init__(self, device, size):
        self.device = device
        self.size = size
        self.index = 0

    def get_free(self):
        segments = []
        marker = 0

        for part in self.partitions:
            if part.start > marker:
                segments.append((marker, part.start))
            marker = part.end_bytes

        if marker < self.size: segments.append((marker, self.size))
        return segments

    def check_overlap(self, start, size):
        end = start + size
        for part in self.partitions:
            if start < part.end and end > part.start:
                return True

        return False

    @property
    def num_partitions(self):
        return len(self.partitions)

    def add_partition(self, fs, size, mountpoint):

        for start,end in self.get_free():
            if self.check_overlap(start, size):
                continue

            if (end - start) >= size:
                self.index += 1

                partition = Partition(
                        index=self.index,
                        fstype=fs,
                        mountpoint=mountpoint,
                        start=start,
                        size=size,
                        end=start+size
                        )

                self.partitions.append(partition)
    
    def resize_partition(self, index, size):
        target = next((p for p in self.partitions if p.index == index), None)

        if not target:
            logger.error(f"No partition at index {index}")
            return False
        
        new_end = target.start + size
        if new_end > self.size:
            logger.error(f"Can't resize partition {index}: Drive capacity reached.")
            return False

        list_index = self.partitions.index(target)
        if list_index + 1 < len(self.partitions):
            next_part = self.partitions[list_index+1]
            if new_end > next_part.start:
                logger.error(f"New partition size for {index} overlaps the next partition.")
                return False

        target.end = new_end
        return True

    def move_partition(self, index, newpos=-1):
        target = next((p for p in self.partitions if p.index == index), None)

        if not target:
            logger.error(f"No partition at index {index}")
            return False

        if newpos != -1:
            return False # TODO: implement

        list_index = self.partitions.index(target)

        if list_index == 0: new_start = 0
        else:
            prev_part = self.partitions[list_index-1]
            new_start = prev_part.end

        if new_start == target.start:
            logger.info("Can't move partition.")
            return False

        size = target.size
        target.start = new_start
        target.end = new_start + size
        return True

    def remove_partition(self, index):
        success = False

        for part in self.partitions:
            if part.index == index:
                self.partitions.remove(part)
                success = True
                break
        
        if self.num_partitions == 0:
            self.index = 0

        return success

class Partman:
    """
    Partition management system
    """

    def __init__(self):
        self.disks = {}

    def add_disk(self, disk, size):
        """
        Register a disk to be tracked by Partman.

        Parameters:
            disk (str): The device file for the disk
            size (int): The size in bytes of the disk
        """
        if not os.path.exists(disk):
            return # Ignore it.

        logger.info(f"Adding disk {disk}")

        diskobj = Disk(disk, size)
        self.disks[disk] = diskobj

    def create_partition(self, disk, fstype, size, mountpoint):
        return self.disks[disk].add_partition(fstype, size, mountpoint)

    def resize_partition(self, disk, partnum, newsize):
        pass

    def move_partition(self, disk, partnum, newstart):
        pass

    def delete_partition(self, disk, partnum):
        pass

    def get_layout(self) -> list:
        for disk in self.disks:
            pass
        pass

    def commit(self):
        pass

# BEGIN: system functions

# `parted` functions

def format_gpt(disk):
    if not os.path.exists(disk):
        logger.error(f"{disk} does not exist.")
        return False

    return run_subprocess(f"parted {disk} --script mklabel gpt")

def format_msdos(disk): # Here for legacy reasons
    if not os.path.exists(disk):
        logger.error(f"{disk} does not exist.")
        return False
    
    return run_subprocess(f"parted {disk} --script mklabel msdos")

def add_partition(disk, fstype, start, end, flags):
    if not os.path.exists(disk):
        logger.error(f"{disk} does not exist.")
        return False

    cmd = f"parted {disk} --script mkpart primary {fstype} {start} {end}"

# Filesystems
def create_filesystem(disk, part, fstype):
    if not os.path.exists(disk):
        logger.error(f"{disk} does not exist.")
        return False

    device_path = f'{disk}{'p' if ('nvme' in disk or 'md' in disk) else ''}{part}'

    cmd = ''

    match fstype:
        case 'ext4':
            cmd = f'mkfs.ext4 {device_path}'
        case 'btrfs':
            cmd = f'mkfs.btrfs -f {device_path}'
        case 'vfat':
            cmd = f'mkfs.vfat {device_path}'
        case _:
            logger.error(f"Unknown filesystem type {fstype}.")
            return False

    return run_subprocess(cmd)
