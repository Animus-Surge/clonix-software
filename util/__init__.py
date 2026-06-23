"""
Clonix: util/__init__.py

Utility functions
"""


import os
import subprocess
import time

from loguru import logger
import psutil

import constants

def log_error(error: subprocess.CalledProcessError, message: str):
    logger.error(message)
    for line in error.stderr().strip().split('\n'):
        logger.trace(line)

def get_part_uuid(mountpoint=None, device=None, by_id=False):
    if mountpoint:
        mountpoint = os.path.abspath(mountpoint)
        device_path = None

        with open("/proc/mounts", 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == mountpoint:
                    device_path = parts[0]
                    break

        if not device_path:
            return None

        uuid_dir = "/dev/disk/by-uuid"

        for uuid in os.listdir(uuid_dir):
            full_uuid_path = os.path.join(uuid_dir, uuid)

            try:
                real_path = os.path.realpath(full_uuid_path)
                if real_path == os.path.realpath(device_path):
                    return uuid
            except OSError: continue
        return None

    if device:
        if by_id:
            target_path = os.path.realpath(device)
            for id in os.listdir("/dev/disk/by-id"):
                id_link = os.path.join("/dev/disk/by-id", id)

                try:
                    if os.path.realpath(id_link) == target_path:
                        return id
                except OSError: continue

        else:
            target_path = os.path.realpath(device)
            for uuid in os.listdir("/dev/disk/by-uuid"):
                uuid_link = os.path.join("/dev/disk/by-uuid", uuid)

                try:
                    if os.path.realpath(uuid_link) == target_path:
                        return uuid
                except OSError: continue
        return None
        

def check_dir_empty(directory):
    if os.path.isdir(directory):
        with os.scandir(directory) as entries:
            for _ in entries:
                return False
            return True
    return True # Ignore it; or error, idk

# FIXME: missing passphrase integration.
def cryptsetup_unlock(device, psp):
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
        subprocess.run(cmd, input=psp, check=True, capture_output=True, text=True)
        time.sleep(5) # Allow it to run

    except subprocess.CalledProcessError as e:
        log_error(e, "Failed to unlock {}".format(device))
        return False

    except InterruptedError:
        logger.trace("Sleep interrupted.")

    if not os.path.exists("/dev/mapper/dm_crypt-0"):
        logger.error("Failed to unlock {}; unknown error.".format(device))
        return False

    return True

def mount_binds(target):
    for dir in ["dev", "proc", "run", "sys"]:
        mount_cmd = ["mount", "--bind", f"/{dir}", os.path.join(target, dir)]
        try:
            subprocess.run(mount_cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to mount {}".format(dir))
            for line in e.stderr.strip().split('\n'):
                logger.trace(line)
            return False
    return True

def mount_device(device, mountpoint, mkdir=True, opts=None):
    if "=" not in device or not os.path.exists(device): # Should allow LABEL=root or UUID=<...> to work in place of device
        logger.error("Cannot mount {}: no such device.".format(device))
        return False

    if not os.path.exists(mountpoint):
        if mkdir:
            os.mkdir(mountpoint)
        else:
            logger.error("Failed to mount {}; mountpoint {} does not exist, and mkdir is False.".format(device, mountpoint))
            return False

    mount_cmd = ["mount"]
    mount_cmd.append(device)
    if opts:
        mount_cmd.append('-o')
        mount_cmd.append(opts)
    mount_cmd.append(mountpoint)

    try:
        subprocess.run(mount_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to mount {}".format(device))
        for line in e.stderr.strip().split('\n'):
            logger.trace(line)
        return False
    return True

def unmount_path(path, recursive=False):
    if os.path.ismount(path):
        try:
            subprocess.run(['umount', "--recursive" if recursive else "", path], check=True)
        except subprocess.CalledProcessError as e:
            logger.error("Failed to unmount {}".format(path))
            for line in e.stderr.strip().split('\n'):
                logger.trace(line)
            return False
        return True

    logger.error("Path {} is not a mountpoint.".format(path))
    return False

## BEGIN: hardware management

def get_physical_drives():
    disks = []

    if not os.path.exists('/sys/block'):
        logger.fatal("This system must be run on *nix systems (Linux, MacOS, etc).")
        exit(1)

    for dev in os.listdir('/sys/block'):
        # Determine if the device is a physical drive
        if dev.startswith(('loop', 'ram', 'zram', 'md', 'dm-')): continue
        if dev.startswith('sr'): continue

        dev_path = os.path.join('/sys/block', dev)

        if not os.path.exists(os.path.join(dev_path, 'device')): continue

        # Get drive information (manufacturer, capacity

        dev_manuf = 'Unknown'
        for name_file in ['device/model', 'device/vendor']:
            full_path = os.path.join(dev_path, name_file)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f: dev_manuf = f.read().strip()
                break

        dev_capac = 0.0
        size_path = os.path.join(dev_path, 'size')
        if os.path.exists(size_path):
            with open(size_path, 'r') as f:
                sectors = int(f.read().strip())
                dev_capac = round((sectors * 512) / (1024**3), 2)

        dev_path = f"/dev/{dev}"
        disks.append((dev_path, dev_manuf, dev_capac))

    return disks

## BEGIN: partition manager

partition_index = 1
partitions = []

# Drive/partition manager; also handles encrypted partition setup
def reformat_drive_uefi(drive):
    # parted {drive} -- mklabel gpt
    # partition_index = 1
    global partition_index
    cmd = ['parted', drive, '--', 'mklabel', 'gpt']
    try:
        subprocess.run(cmd, input=constants.YES, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to reformat {} as gpt.".format(drive))
        for line in e.stderr.strip().split('\n'):
            logger.trace(line)
        return False
    partition_index = 1
    return True


def make_partition(drive: str, fstype: str, start: str, end: str, flags=0):
    global partition_index
    # parted {drive} -- mkpart primary {fstype} {start} {end}
    # for each flag:
    #    parted {drive} -- set {partition_index} {flag} on
    # partition_index++

    prefix = "p" if "nvme" in drive else ""

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
        return -1

    # Flags step

    # Skip this step entirely; saves overhead
    flags_enabled = []
    if flags != 0: 
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
                        return -1

    logger.info("Created partition {} as {}. Enabled flags: {}".format(partition_index, fstype, ','.join(flags_enabled)))

    index = partition_index
    partition_index += 1
    partitions.append(f"{drive}{prefix}{index}")
    return index
    
# TODO: support more format options; i.e. ntfs, fat[8,16,32], etc.
def format_crypt(partition: int, psp: str, cryptname: str):
    """
    Format and open a LUKS volume
    """

    cmd = ['cryptsetup', 'luksFormat', '-q', partitions[partition-1]]
    cmd2 = ['cryptsetup', 'luksOpen', partitions[partition-1], cryptname] # Adding cryptname here should allow for easy testing on existing encrypted systems
    try:
        subprocess.run(cmd, input=psp, check=True, capture_output=True, text=True)
        time.sleep(2)
        subprocess.run(cmd2, input=psp, check=True, capture_output=True, text=True)
        time.sleep(2)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to format {} as crypt.".format(partition))
        for line in e.stderr.strip().split('\n'):
            logger.trace(line)
        return False
    return True

def format_ext4(partition: int):
    cmd = ['mkfs.ext4', partitions[partition-1]]
    try:
        subprocess.run(cmd, input=constants.YES, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to format {} as ext4.".format(partition))
        for line in e.stderr.strip().split('\n'):
            logger.trace(line)
        return False
    return True

def format_btrfs(partition: int):
    cmd = ['mkfs.btrfs', '-f', partitions[partition-1]]
    try:
        subprocess.run(cmd, input=constants.YES, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to format {} as btrfs.".format(partition))
        for line in e.stderr.strip().split('\n'):
            logger.trace(line)
        return False
    return True

def format_vfat(partition: int):
    cmd = ['mkfs.vfat', '-F', '32', partitions[partition-1]]
    try:
        subprocess.run(cmd, input=constants.YES, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error("Failed to format {} as vfat.".format(partition))
        for line in e.stderr.strip().split('\n'):
            logger.trace(line)
        return False
    return True

