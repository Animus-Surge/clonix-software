"""
Clonix: handlers/filesystem.py

Filesystem operations
"""

import os

import util

from loguru import logger

def mkfs(target, fstype):
    if not os.path.exists(target):
        logger.error(f"{target} does not exist.")
        return False

    cmd = ''

    match fstype:
        case 'ext4':
            cmd = f'mkfs.ext4 {target}'
        case 'btrfs':
            cmd = f'mkfs.btrfs -f {target}'
        case 'vfat':
            cmd = f'mkfs.vfat {target}'
        case _:
            logger.error(f"Unknown filesystem type {fstype}.")
            return False

    return util.run_subprocess(cmd)

def btrfs_defragment(target):
