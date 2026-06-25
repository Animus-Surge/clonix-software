"""
Clonix: deploy/partition.py

Partition system for deploying systems
"""

import util
from util import constants

from loguru import logger

# TODO: custom

def mk_parts(drives: list[str], dep_type: int, psp: str | None):

    # Drives (list): first drive boot, second dependent on dep_type. In format /dev/<device>
    # dep_type: If 2 (custom), drives is expected to be a dictionary

    match dep_type:
        case -1:
            logger.error("Custom setup not supported yet.")
            return False

        case 0:
            # Standard deployment:
            # Target is drives index 0
            # dev1: 512M fat32, esp; /boot/efi
            # dev2: 2G ext4; /boot
            # dev3: 100% btrfs (encrypted); /
            # Plus subvolumes (handled after copy operation)

            if not psp:
                logger.error("Encrypted deployment requires passphrase.")
                return False

            target = drives[0]

            if not util.reformat_drive_uefi(target): return False

            if not util.make_partition(
                    target, 'fat32', '8M', '512M', 
                    constants.PART_FLAGS.get("esp", 0)): return False
            if not util.make_partition(target, 'ext4', '512M', '2G'): return False
            if not util.make_partition(target, 'btrfs', '2G', '100%'): return False

            if not util.format_vfat(1): return False
            if not util.format_ext4(2): return False
            if not util.format_crypt(3, psp, 'dm_crypt-0'): return False
            if not util.format_btrfs(4): return False

            return True

        case _:
            logger.error("Unknown deployment type.")
            return False
