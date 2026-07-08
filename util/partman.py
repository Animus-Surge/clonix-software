"""
Clonix: util/partman.py

Partition manager
"""

import os
import re
from dataclasses import dataclass, asdict, field
from typing import Optional, Union, Dict, List

from loguru import logger

from util import constants, get_drive_size_raw, get_physical_drives, run_subprocess, gvars, convert

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
    flags: List[str] = field(default_factory=list) # Flag names

class Disk:
    size: int
    label: str = 'gpt' # Default to a UEFI boot record format
    partitions: List[Partition]

    def __init__(self, device, size):
        self.device = device
        self.size = size
        self.index = 0
        self.partitions = []

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

    def get_free_size(self, start: int):
        free = self.get_free_space()

        for f_start,f_end in free:
            if f_start <= start and start <= f_end:
                return f_end - start

        return 0

    def get_layout(self):
        return { 'device': self.device, 'size': self.size, 'partitions': [asdict(part) for part in self.partitions] }

    # Partition management
    def create_partiiton(self, fstype: str, start: int, end: int, mountpoint: str):
        size = end - start
        for f_start,f_end in self.get_free_space():
            if (f_end - f_start) >= size:
                self.index += 1

                partition = Partition(self.index, fstype, mountpoint, start, size, start+size)

                self.partitions.append(partition)
                self._reorganize()

                return True

        return False

    def remove_partition(self, index: int):
        if index > len(self.partitions):
            logger.error("Partition index out of bounds.")
            return False

        del self.partitions[index]
        self._reorganize()

        return True

    def set_partition_flags(self, index: int, flags: int, unset=False):
        if index >= len(self.partitions):
            logger.error("Partition index out of bounds.")
            return False

        target = self.partitions[index]

        # Ignore if flags is zero
        if flags == 0: return True # Failed successfully!

        for flag in constants.PART_FLAGS.items():
            if flags & flag[1]:
                if unset and flag[0] in target.flags:
                    target.flags.remove(flag[0])
                elif not unset and not flag[0] in target.flags: # Should fix if this function gets called multiple times
                    target.flags.append(flag[0])

        return True

    def set_partition_encrypt(self, index: int, encrypt: bool):
        if index >= len(self.partitions):
            logger.error("Partition index out of bounds.")
            return False

        target = self.partitions[index]
        target.encrypted = encrypt
        return True

class Partman:
    disks: List[Disk]

    def __init__(self, with_detected=True):
        """
        Create a new partition manager instance.

        Parameters:
            with_detected (bool): True: Populate `self.disks` with the detected drives
        """
        self.disks = []

        if with_detected:
            for disk in get_physical_drives():
                self.disks.append(Disk(disk[0], disk[2]))

    # Viewing
    def get_disks(self):
        """
        Get what disks are being tracked

        To get all information about the disk, use `get_layout`

        Returns:
            list: List of drive devices (str)
        """
        return [disk.device for disk in self.disks]

    def get_disk(self, disk: str | int):
        target: Disk | None = None
        if isinstance(disk, int):
            if disk >= 0 and disk < len(self.disks):
                target = self.disks[disk]
            else:
                logger.error('Disk out of range.')
                return False
        else:
            target = next((drive for drive in self.disks if drive.device == disk), None)

        return target

    def get_layout(self):
        """
        Get the complete partition layout.

        Returns:
            list: List of drives (dicts), with their partitions
        """
        layout = []
        for disk in self.disks:
            if len(disk.partitions) > 0:
                layout.append(disk.get_layout())
        return layout

    def get_summary(self, as_list=False):
        if as_list:
            pass

        for disk in self.get_disks():
            for part in disk.partitions:
                print(f'{disk.device}: {part.index} {part.fstype} - {raw_to_readable(part.start)}-{raw_to_readable(part.end)} ({raw_to_readable(part.size)} - {part.mountpoint}')

    # Management
    def add_disk(self, disk: str):
        """
        Track a disk in partman.

        Ex. /dev/sdc, /dev/nvme0n1

        Parameters:
            disk (str): The disk to track

        Returns:
            bool: True if successful
        """
        if not os.path.exists(disk):
            return False

        disk_obj = Disk(disk, get_drive_size_raw(disk))
        self.disks.append(disk_obj)
        return True

    def add_partition(self, disk: str | int, fstype: str, start: str | int, end: str | int, mountpoint: str):
        """
        Create a partition on the specified disk.

        Parameters:
            disk (str | int): Device name or disk index to create the partition on
            fstype (str): The filesystem type to use with parted
            size (str | Int): Human-readable or raw byte count size for the partition
            mountpoint (str): The mountpoint of the disk. Blank means no mountpoint.

        Returns:
            bool: True if successful.
        """
        target = self.get_disk(disk)

        if not target:
            logger.error("Could not find disk.")
            return False

        if isinstance(start, str):
            start = readable_to_raw(start)

        free_size = target.get_free_size(start)
        if free_size == 0: 
            logger.error("Partition start point overlaps with existing partition.")
            return False

        if isinstance(end, str):
            end = readable_to_raw(end, free_size)

        return target.create_partiiton(fstype, start, end, mountpoint)

    def remove_partition(self, disk: str | int, index: int):
        """
        Remove a partition on the specified disk.

        Parameters:
            disk (str | int): Device name or disk index to remove the partition on
            index (int): The partition index

        Returns:
            bool: True if successful.
        """
        target = self.get_disk(disk)

        if not target:
            logger.error("Could not find disk.")
            return False
        
        return target.remove_partition(index)

    def reset(self):
        """
        Reset the partition layout to empty.
        """
        for disk in self.disks:
            disk.partitions = []

    def set_encrypted(self, disk: str | int, index: int):
        target = self.get_disk(disk)
        if not target:
            logger.error("Could not find disk.")
            return False

        return target.set_partition_encrypt(index, True)

    def unset_encrypted(self, disk: str | int, index: int):
        target = self.get_disk(disk)
        if not target:
            logger.error("Could not find disk.")
            return False

        return target.set_partition_encrypt(index, False)

    def set_mountpoint(self, disk: str | int, index: int, mountpoint: str):
        target = self.get_disk(disk)
        if not target:
            logger.error("Could not find disk.")
            return False

        if index >= len(target.partitions):
            logger.error("Partition index out of bounds.")
            return False

        target.partitions[index].mountpoint = mountpoint
        return True

    def set_flag(self, disk: str | int, index: int, flags: int):
        target = self.get_disk(disk)

        if not target:
            logger.error("Could not find disk.")
            return False

        return target.set_partition_flags(index, flags)

    def unset_flag(self, disk: str | int, index: int, flags: int):
        target = self.get_disk(disk)
        if not target:
            logger.error("Could not find disk.")
            return False

        return target.set_partition_flags(index, flags, True)

    # Runner
    def commit(self, passphrase=""):
        """
        Run the partition setup.

        Encrytped volumes will use provided passphrase.

        Parameters:
            passphrase (str): The passphrase to use for encrypted volumes
        """
        logger.info("Starting partman commit...")

        for disk in self.disks:
            # Start with reformat
            device = disk.device

            if not format_gpt(device):
                logger.error(f"Failed to create GPT on {device}.")
                continue # We can still format the rest of the drives if they exist!
            
            index = 1
            for partition in disk.partitions:
                if not add_partition(device, index, partition.fstype, partition.start, partition.end, partition.flags):
                    logger.error(f"Failed to create partition {index} on {device}.")
                    return False

                fs = partition.fstype
                if partition.encrypted:
                    fs = f'encrypt:{partition.fstype}'

                if not create_filesystem(device, index, fs, passphrase):
                    logger.error(f"Failed to create filesystem on partition {index} on {device}.")
                    return False
                
                index += 1
            logger.info(f"Formatted {device}.")

        return True

'''
Example layout:

[
    {
        "device": "/dev/sda"
        "partitions": [
            {
                "fstype": "vfat",
                "start": "8M",
                "end": "512M",
                "mountpoint": "/boot/efi"
            },
            {
                "fstype": "ext4",
                "start": "512M",
                "end": "2G",
                "mountpoint": "/boot"
            },
            {
                "fstype": "btrfs",
                "encrypted": true",
                "start": "2G",
                "end": "100%",
                "mountpoint": "/"
            }
        ]
    }
]

'''

def run_partman(layout: list):
    """
    Run a partman instance, given layout. Intended for automated installs.
    """

    partman = Partman()

    registered_devices = [disk.device for disk in partman.get_disks()]

    for drive in layout:
        device = drive.get('device')

        

    pass

def run_partman_tui():
    """
    Run the standalone TUI application for partman.
    """
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

# Partition management
def add_partition(disk: str, index: int, fstype: str, start: int, end: int, flags: list[str]):
    if not os.path.exists(disk):
        logger.error(f"{disk} does not exist.")
        return False

    if not run_subprocess(f"parted {disk} --script mkpart primary {fstype} {start} {end}"): return False

    # Flags
    for flag in flags:
        if not run_subprocess(f"parted {disk} --script set {index} {flag} on"):
            return False

    return True

def create_encrypted_volume(disk: str, index: int):
    if not os.path.exists(disk):
        logger.error(f'{disk} does not exist.')
        return False

    psp = gvars.ENC_PASSPHRASE

    pass

def create_filesystem(disk: str, index: int, filesystem: str):
    prefix=('p' if 'nvme' in disk or 'md' in disk else '')
    full_path = f'{disk}{prefix}{index}'

    if not os.path.exists(full_path):
        logger.error(f"Partition {full_path} does not exist.")
        return False

    if 'encrypt' in filesystem:
        pass

    cmd = ""

    match filesystem:
        case 'btrfs':
            cmd = f"mkfs.btrfs -f {full_path}"
        case 'ext4':
            cmd = f"mkfs.ext4 {full_path}"
        case 'vfat' | 'fat32':
            # Using vfat regardless. fat32 is provided to parted.
            cmd = f"mkfs.vfat -F 32 {full_path}"
        case _:
            logger.error(f"Unknown filesystem type: {filesystem}")
            return False

    return run_subprocess(cmd)
