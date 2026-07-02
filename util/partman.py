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
import constants

BYTE_MULTIPLIERS = {
        'K': 1024,
        'M': 1024**2,
        'G': 1024**3,
        'T': 1024**4,
        'P': 1024**5
}

def raw_to_readable(value: int) -> str:
    if value <= 0: return '0B' # Just give zero bytes for negative and zero values
    size = float(value)
    
    index = 0
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB']

    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1

    if index == 0: return f'{int(size)}B'
    return f'{size:.2f}{units[index]}'

def readable_to_raw(value: str, size: int = 0) -> int:
    value = value.strip().upper()

    # Percentage checking
    if '%' in value:
        if size == 0: return 0

        percentage = float(value.rstrip('%'))
        return int((percentage / 100.0) * size)

    # Everything else (i.e. 500GB, 7TIB, 1000P)
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([KMGTPE]I?B?)?$', value)
    if not match:
        logger.error("Value error in conversion from readable size to raw bytes.")
        return 0

    number, unit = match.groups()
    number = float(number)

    if not unit: return int(number)

    unit = unit[0] # Get first letter of unit

    return int(number * BYTE_MULTIPLIERS.get(unit, 1))

def get_uuid():
    pass

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

    # Optional fields
    label: str = ''  # Drive labels?
    dev_name: str = '' # i.e. nvme0n1p4 or sda2, or md126p2. 
    encrypted: bool = False

    def __repr__(self):
        return f'{self.index} - {self.dev_name}: {self.label} {raw_to_readable(self.size)} ({self.start} - {self.end}) {self.fstype} {self.mountpoint}'


class Disk:
    size: int
    label: str = 'gpt' # Default to a UEFI boot record format
    partitions: list

    def __init__(self, device, size):
        self.device = device
        self.size = size
        self.index = 0

    def _reorganize(self):
        # Start by sorting
        self.partitions.sort(key=lambda p: p.start)

        # Re-index
        index = 1
        for part in self.partitions:
            part.index = index
            index += 1

        self.index = index - 1 # Reset current index

    def get_free_space(self):
        segments = []
        marker = 0

        for part in self.partitions:
            if part.start > marker:
                segments.append((marker, part.start))
            marker = part.end

        if marker < self.size:
            segments.append((marker, self.size))

        return segments

    # Partition management
    def create_partiiton(self, fstype, size, mountpoint):
        for start,end in self.get_free_space():
            if (end - start) >= size:
                self.index += 1

                partition = Partition(self.index, fstype, mountpoint, start, size, start+size)

                self.partitions.append(partition)
                self._reorganize()

                return True

        return False

    def remove_partition(self, index):
        if index > len(self.partitions):
            logger.error("Partition index out of bounds.")
            return False

        del self.partitions[index]
        self._reorganize()

        return True

    def resize_partition(self, index, new_size):
        if index > len(self.partitions):
            logger.error("Partition index out of bounds.")
            return False

        target = self.partitions[index]

        if target.end == self.size:
            logger.error("Cannot resize, target partition ends at drive capacity.")
            return False

        if target.start+new_size > self.size:
            logger.error("Cannot resize, new size exceeds capacity.")
            return False

        target.size = new_size
        target.end = target.start + new_size
        return True

    def move_partition(self, index, new_start=-1):
        if index > len(self.partitions):
            logger.error("Partition index out of bounds.")
            return False

        target = self.partitions[index]

        for start,end in self.get_free_space():
            if target.start > start and target.start <= end: # Found our position
                if new_start == -1: # Special case: move partition to start of free space
                    target.start = start
                    target.end = start + target.size
                    return True

                if new_start >= start:
                    target.start = new_start
                    target.end = new_start + target.size
                    return True

        return False

class Partman:
    def __init__(self):
        pass

    # Viewing
    def get_disks(self):
        pass

    def get_layout(self):
        pass

    def add_disk(self):
        pass

    # Management
    def add_partition(self):
        pass

    def remove_partition(self):
        pass

    def move_partition(self):
        pass
    
    def resize_partition(self):
        pass

    def encrypt_partition(self):
        pass

    def set_mountpoint(self):
        pass

    # Runner
    def commit(self):
        pass

def run_partman():
    pass

def run_partman_tui():
    pass

# BEGIN: system functions
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

def add_partition(disk, index, fstype, start, end, flags):
    if not os.path.exists(disk):
        logger.error(f"{disk} does not exist.")
        return False

    if not run_subprocess(f"parted {disk} --script mkpart primary {fstype} {start} {end}"): return False

    # Flags
    if flags != 0:
        for flag in constants.PART_FLAGS.items():
            if flags & flag[1]:
                if not run_subprocess(f'parted {disk} -- set {index} {flag[0]} on'): return False

    return True
