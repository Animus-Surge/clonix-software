"""
Clonix: util/__init__.py

Utility functions
"""


import os
import subprocess
import time

from loguru import logger

import constants


def check_dir_empty(directory):
    if os.path.isdir(directory):
        with os.scandir(directory) as entries:
            for _ in entries:
                return False
            return True
    return True # Ignore it; or error, idk

# FIXME: missing passphrase integration.
def cryptsetup_unlock(device):
    if not os.path.exists(device):
        logger.error("Cannot unlock {}: no such device.".format(device))
        return False

    cmd = [
            'cryptsetup',
            'luksOpen',
            device,
            'dm_crypt-0'
            ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        time.sleep(5)

    except subprocess.CalledProcessError as e:
        logger.error("Failed to unlock {}".format(device))
        for line in e.stderr.strip().split('\n'):
            logger.trace(line)
        return False

    except InterruptedError:
        logger.trace("Sleep interrupted.")

    if not os.path.exists("/dev/mapper/dm_crypt-0"):
        logger.error("Failed to unlock {}; unknown error.".format(device))
        return False

    return True

def mount_device(device, mountpoint, mkdir=True, opts=None):
    if not os.path.exists(device):
        logger.error("Cannot mount {}: no such device.".format(device))
        return False

    if not os.path.exists(mountpoint):
        if mkdir:
            os.mkdir(mountpoint)
        else:
            logger.error("Failed to mount {}; mountpoint {} does not exist, and mkdir is False.".format(device, mountpoint))
            return False

    mount_cmd = ["mount"]
    if opts:
        mount_cmd.append('-o')
        mount_cmd.append(opts)
    mount_cmd.append(device)
    mount_cmd.append(mountpoint)

    try:
        subprocess.run(mount_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to mount {}".format(device))
        for line in e.stderr.strip().split('\n'):
            logger.trace(line)
        return False
    return True

def unmount_path(path):
    if os.path.ismount(path):
        try:
            subprocess.run(['umount', path], check=True)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to unmount {}".format(path))
            for line in e.stderr.strip().split('\n'):
                logger.trace(line)
            return False
        return True

    logger.error("Path {} is not a mountpoint.".format(path))
    return False

partition_index = 1

# Drive/partition manager; also handles encrypted partition setup
def reformat_drive_uefi(drive):
    # parted {drive} -- mklabel gpt
    # partition_index = 1
    cmd = ['parted', drive, '--', 'mklabel', 'gpt']
    try:
        subprocess.run(cmd, input=constants.YES, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to reformat {} as gpt.".format(drive))
        for line in e.stderr.strip().split('\n'):
            logger.trace(line)
        return False


def make_partition(drive, fstype, start, end, flags):
    # parted {drive} -- mkpart primary {fstype} {start} {end}
    # for each flag:
    #    parted {drive} -- set {partition_index} {flag} on
    # partition_index++

    # Partition step
    cmd_partition = [
            'parted', drive,
            '--',
            'mkpart', 'primary', fstype, start, end
            ]
    try:
        subprocess.run(cmd_partition, input=constants.YES, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to create partition {} as {} on {}.".format(partition_index, fstype, drive))
        for line in e.stderr.strip().split('\n'):
            logger.trace(line)
        return False

    # Flags step

    # Skip this step entirely; saves overhead
    if flags == 0: 
        logger.info("Created partition {} as {}.".format(partition_index, fstype))
        return True

    flags_enabled = []

    for flag in constants.PART_FLAGS.items():
        if flags & flag[1]:
            flag_cmd = ['parted', drive, '--', 'set', str(partition_index), flag[0], 'on']
            
            try:
                subprocess.run(flag_cmd, check=True, text=True, capture_output=True)
                flags_enabled.append(flag[0])
            except subprocess.CalledProcessError as e:
                logger.error("Failed to run flag {} ({}) on index {}.".format(flag[0], flag[1], partition_index))
                for line in e.stderr.strip().split('\n'):
                    logger.trace(line)
                    return False

    logger.info("Created partition {} as {}. Enabled flags: {}".format(partition_index, fstype, ','.join(flags_enabled)))
    return True
    
# TODO: support more format options; i.e. ntfs, fat[8,16,32], etc.
def format_crypt(partition, psp, cryptname):
    """
    Format and open a LUKS volume
    """

    cmd = ['cryptsetup', 'luksFormat', '-q', partition]
    cmd2 = ['cryptsetup', 'luksOpen', partition, cryptname] # Adding cryptname here should allow for easy testing on existing encrypted systems
    try:
        subprocess.run(cmd, input=psp, check=True, capture_output=True, text=True)
        subprocess.run(cmd2, input=psp, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to format {} as crypt.".format(partition))
        for line in e.stderr.strip().split('\n'):
            logger.trace(line)
        return False
    return True

def format_ext4(partition):
    cmd = ['mkfs.ext4', partition]
    try:
        subprocess.run(cmd, input=constants.YES, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to format {} as ext4.".format(partition))
        for line in e.stderr.strip().split('\n'):
            logger.trace(line)
        return False
    return True

def format_btrfs(partition):
    cmd = ['mkfs.btrfs', '-f', partition]
    try:
        subprocess.run(cmd, input=constants.YES, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to format {} as btrfs.".format(partition))
        for line in e.stderr.strip().split('\n'):
            logger.trace(line)
        return False
    return True

def format_vfat(partition):
    cmd = ['mkfs.vfat', '-F', '32', partition]
    try:
        subprocess.run(cmd, input=constants.YES, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to format {} as vfat.".format(partition))
        for line in e.stderr.strip().split('\n'):
            logger.trace(line)
        return False
    return True

