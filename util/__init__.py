"""
Clonix: util/__init__.py

Utility functions
"""


import os
import re
import shlex
import subprocess
import time

import httpx
from loguru import logger

import constants

def log_error(error: Exception, message: str):
    
    if type(error) is subprocess.CalledProcessError:
        logger.error(f"{message} ({error.returncode})")
        for line in error.stderr().strip().split('\n'):
            logger.trace(line)

    else:
        logger.error(f"{message}")
        for line in error.args:
            pass

def run_subprocess(cmd: list | str, prepend=[], user_input=""):
    final_cmd=prepend
    for x in (shlex.split(cmd) if cmd is str else cmd): final_cmd.append(x)

    logger.debug(f"Running: `{' '.join(final_cmd)}`")

    try:
        output = subprocess.run(final_cmd, check=True, capture_output=True, text=True, input=user_input)
        logger.debug(output.stdout)
    except subprocess.CalledProcessError as e:
        log_error(e, f"Command failure: `{' '.join(final_cmd)}`")
        return False

    return True

def run_chroot_process(cmd: list | str, root="/target", prepend=[], user_input=""):
    final_cmd = prepend
    for x in ["chroot", root, "/bin/bash"]: final_cmd.append(x)
    for x in (shlex.split(cmd) if cmd is str else cmd): final_cmd.append(x)

    return run_subprocess(cmd, user_input=user_input)
    


def get_part_uuid(mountpoint=None, device=None, by_id=False) -> str | None:
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
        

def check_dir_empty(directory) -> bool:
    if os.path.isdir(directory):
        with os.scandir(directory) as entries:
            for _ in entries:
                return False
            return True
    return True # Ignore it; or error, idk

def cryptsetup_unlock(device, psp) -> bool:
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

def mount_binds(target) -> bool:
    for dir in ["dev", "proc", "run", "sys"]:
        if not run_subprocess(f"mount --bind {dir} {os.path.join(target, dir)}"): return False
    return True

def mount_device(device, mountpoint, mkdir=True, opts=None) -> bool:
    if "=" not in device or not os.path.exists(device): # Should allow LABEL=root or UUID=<...> to work in place of device
        logger.error(f"Cannot mount {device}: no such device.")
        return False

    if not os.path.exists(mountpoint):
        if not mkdir:
            logger.error(f"Failed to mount {device}: mountpoint does not exist. (mkdir=False)")
            return False
        os.mkdir(mountpoint)
    
    mount_cmd = f"mount {f'-o{opts}' if opts else ''} {device} {mountpoint}"

    return run_subprocess(mount_cmd)

def unmount_path(path, recursive=False) -> bool:
    if os.path.ismount(path):
        return run_subprocess(f"umount {'--recursive' if recursive else ''} {path}")

    logger.error("Path {} is not a mountpoint.".format(path))
    return False

## BEGIN: hardware management

def get_physical_drives() -> list:
    disks = []

    if not os.path.exists('/sys/block'):
        logger.critical("This system must be run on *nix systems (Linux, MacOS, etc).")
        return []

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

def get_drive_size_raw(device):
    device_name = os.path.basename(device)
    sys_path = f"/sys/class/block/{device_name}/size"

    with open(sys_path, 'r') as f: return int(f.read().strip()) * 512

## BEGIN: Partition and filesystem manager

partition_index = 1
partitions = []

# DEPRECATED: Moved to partman.py


# Drive/partition manager; also handles encrypted partition setup
def reformat_drive_uefi(drive) -> bool:
    # parted {drive} -- mklabel gpt
    # partition_index = 1
    global partition_index
    cmd = ['parted', drive, '--', 'mklabel', 'gpt']
    try:
        subprocess.run(cmd, input=constants.YES, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        log_error(e, f"Failed to reformat {drive} as GPT.")
        return False
    partition_index = 1
    return True


def make_partition(drive: str, fstype: str, start: str, end: str, flags=0) -> int:
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
        log_error(e, f"Failed to create partition {partition_index} as {fstype} on {drive}.")
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
                    log_error(e, f"Failed to run flag {flag[0]} ({flag[1]}) on index {partition_index}.")
                    return -1

    logger.info("Created partition {} as {}. Enabled flags: {}".format(partition_index, fstype, ','.join(flags_enabled)))

    index = partition_index
    partition_index += 1
    partitions.append(f"{drive}{prefix}{index}")
    return index
    
# TODO: support more format options; i.e. ntfs, fat[8,16,32], etc.
def format_crypt(partition: int, psp: str, cryptname: str) -> bool:
    """
    Format and open a LUKS volume
    """

    cmd = ['cryptsetup', 'luksFormat', '-q', partitions[partition-1], '-']
    cmd2 = ['cryptsetup', 'luksOpen', partitions[partition-1], cryptname, '-'] # Adding cryptname here should allow for easy testing on existing encrypted systems
    try:
        subprocess.run(cmd, input=psp, check=True, capture_output=True, text=True)
        time.sleep(2)
        subprocess.run(cmd2, input=psp, check=True, capture_output=True, text=True)
        time.sleep(2)
    except subprocess.CalledProcessError as e:
        log_error(e, f"Failed to format {partition} as crypt.")
        return False
    partitions.append(f"/dev/mapper/{cryptname}") # Add this so other formatters can format the encrypted partition
    return True

def format_ext4(partition: int) -> bool:
    cmd = ['mkfs.ext4', partitions[partition-1]]
    try:
        subprocess.run(cmd, input=constants.YES, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        log_error(e, f"Failed to format {partition} as ext4.")
        return False
    return True

def format_btrfs(partition: int) -> bool:
    cmd = ['mkfs.btrfs', '-f', partitions[partition-1]]
    try:
        subprocess.run(cmd, input=constants.YES, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        log_error(e, f"Failed to format {partition} as btrfs.")
        return False
    return True

def format_vfat(partition: int) -> bool:
    cmd = ['mkfs.vfat', '-F', '32', partitions[partition-1]]
    try:
        subprocess.run(cmd, input=constants.YES, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        log_error(e, f"Failed to format {partition} as vfat.")
        return False
    return True

def btrfs_defragment(target_path: str) -> bool:
    logger.info(f"Defragmenting {target_path}...")

    return run_subprocess(f"btrfs filesystem defragment -rczstd {target_path}")

# BEGIN: Boot order management
def clear_boot_order(keep_windows=False) -> bool:
    logger.info("Clearing UEFI boot order...")
    if keep_windows: logger.info("Keeping Windows entries")
    try:
        result = subprocess.run(["efibootmgr"], capture_output=True, text=True, check=True)
        output = result.stdout

    except subprocess.CalledProcessError as e:
        log_error(e, "Failed to gather EFI boot order information.")
        return False

    boot_pattern = re.compile(r"^Boot([0-9A-Fa-f]{4})\*?\s+(.*)$")

    for line in output.splitlines():
        match = boot_pattern.match(line)

        if match:
            entry = match.group(1)
            label = match.group(2)

            if label in "Windows Boot Manager" and keep_windows:
                logger.info(f"Keeping {entry}: Windows")
                continue

            if label in ("UEFI", "ONBOARD"):
                logger.info(f"Keeping {entry}: UEFI or Onboard")
                continue

            logger.info(f"Removing {entry}")
            if not remove_boot_entry(entry): return False

    logger.info("Cleared boot order.")
    return True

def remove_boot_entry(entry: str) -> bool:
    try:
        subprocess.run(["efibootmgr", "-b", entry, "-B"], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        log_error(e, f"Failed to remove {entry} from UEFI boot order.")
        return False
    return True

def add_boot_entry(target: str, label: str, path: str) -> bool:
    logger.info(f"Creating boot entry for {target}: {label} - {path}")
    try:
        subprocess.run(["efibootmgr", "-c", "-d", target, "-p", "1", "-L", label, "-l", path], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        log_error(e, f"Failed to create boot entry for {target}.")
        return False
    return True

# BEGIN: server communications

def get_image_metadata(image_name: str) -> dict:
    r = httpx.get(constants.CLONIX_API_URL, params={"image": image_name})

    if r.status_code == 200:
        return {"type": "response", "data": r.json()}
    else:
        return {"type": "error", "reason": "Status code.", "status_code": r.status_code}

# BEGIN: File operations

def copy_file(source: str, target: str) -> bool:
    if not os.path.exists(source):
        logger.error(f"File {source} does not exist.")
        return False

    source_text = []
    with open(source, 'r') as f:
        source_text = f.readlines()

    try:
        with open(target, 'w') as f:
            f.writelines(source_text)

    except OSError as e:
        log_error(e, f"Failed to copy {source} to {target}.")
        return False

    return True
