"""
Clonix: util/__init__.py

Utility functions
"""


import base64
import json
import os
import re
import shlex
import subprocess
import time
from itertools import cycle
from typing import Tuple

import httpx
from dotenv import load_dotenv
from loguru import logger

from . import constants, gvars

# MOVEME

# Encryption functions (obfuscates values to hide them from prying eyes)
## NOTE: These functions should NOT replace actual encryption.
#def encrypt_text(value: str) -> str:
#    v_bytes = value.encode('utf-8')
#    key = gvars.ENC_MASTER_KEY
#    encrypted = bytes(a ^ b for a, b in zip(v_bytes, cycle(key)))
#    return base64.b64encode(encrypted).decode('utf-8')
#
#def decrypt_text(value: str) -> str:
#    v_bytes = base64.b64decode(value.encode('utf-8'))
#    key = gvars.ENC_MASTER_KEY
#    decrypted = bytes(a ^ b for a,b in zip(v_bytes, cycle(key)))
#    return decrypted.decode('utf-8')
#
#def load_key_from_env(): # Loads the master obfuscation key
#    if not load_dotenv():
#        logger.warning("Could not load .env file. Using system env")
#
#    var = os.getenv('ENC_MASTER_KEY')
#    if not var:
#        logger.error("System env does not contain required variable 'ENC_MASTER_KEY'")
#    else:
#        logger.info("Loaded master key from env.")
#        gvars.ENC_MASTER_KEY = var.encode('utf-8')

# Log functions
def log_error(error: Exception, message: str):
    if type(error) is subprocess.CalledProcessError:
        logger.error(f"{message} ({error.returncode})")
        for line in error.stderr.strip().split('\n'):
            logger.trace(line)

    else:
        logger.error(f"{message}")
        for line in error.args:
            pass

# Subprocess functions
def run_subprocess(cmd: list | str, prepend=[], user_input=""):
    logger.debug(cmd)

    final_cmd = []

    # Join command
    for x in prepend: final_cmd.append(x)
    for x in (shlex.split(cmd) if isinstance(cmd, str) else cmd): final_cmd.append(x)

    if constants.DRY_RUN:
        logger.info(f"DRY_RUN{f'(input={user_input})'}: {' '.join(final_cmd)}")
        return True

    logger.info(f"Running: `{' '.join(final_cmd)}`")

    try:
        output = subprocess.run(final_cmd, check=True, capture_output=True, text=True, input=user_input)
        logger.debug(output.stdout)
    except subprocess.CalledProcessError as e:
        log_error(e, f"Command failure: `{' '.join(final_cmd)}`")
        return False
    except FileNotFoundError as e:
        log_error(e, f"Command failure (FileNotFoundError): `{' '.join(final_cmd)}`")
        return False
    except PermissionError as e:
        log_error(e, f"Command failure (PermissionError): `{' '.join(final_cmd)}`")
        return False

    return True

def run_chroot_process(cmd: list | str, root="/target", prepend=[], user_input=""):
    final_cmd = prepend
    for x in ["chroot", root, "/bin/bash"]: final_cmd.append(x)
    for x in (shlex.split(cmd) if isinstance(cmd, str) else cmd): final_cmd.append(x)

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

def unlock_encrypted_partition(device, psp, volname='dm_crypt-0') -> Tuple[bool, str]:
    if not os.path.exists(device):
        logger.error(f"Cannot unlock {device}: no such device.")
        return False, ''

    vol_index = 0
    while os.path.exists(os.path.join("/dev/mapper", volname)):
        vol_index += 1
        volname = f'dm_crypt-{vol_index}'

    if not run_subprocess(f'cryptsetup luksOpen {device} {volname}', user_input=psp): return False, ''
    try:
        time.sleep(2)
    except InterruptedError:
        logger.trace("Sleep interrupted.")

    return True, volname

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


## BEGIN: file management functions
def load_file(path: str) -> str:
    if not os.path.exists(path):
        logger.error(f"Cannot open file: {path} does not exist.")
        return ""
    
    with open(path, 'r') as f:
        return f.read()

def load_file_json() -> dict:
    return {}

def load_system_data() -> dict:
    # Load information from /sys/class/dmi
    serial_number = ""
    manufacturer = ""
    product_name = ""

    with open('/sys/class/dmi/id/product_serial', 'r') as f:
        serial_number = f.read()

    with open('/sys/class/dmi/id/sys_vendor', 'r') as f:
        manufacturer = f.read()

    with open('/sys/class/dmi/id/product_name', 'r') as f:
        product_name = f.read()
    
    return {
        "serial_number": serial_number,
        "manufacturer": manufacturer,
        "product_name": product_name
        }

def read_os_version(source: str = "") -> dict:
    os_version_dict = {}
    try:
        with open(f"${source}/etc/os-release", "r") as f:
            for line in f:
                parts = line.split("=")
                os_version_dict[parts[0]] = parts[1].strip('"')

    except OSError as e:
        log_error(e, "Failed to read `/etc/os-release`")
        return {}

    return os_version_dict

## BEGIN: hardware management

def get_physical_drives() -> list:
    disks = []

    if not os.path.exists('/sys/block'):
        logger.critical("This system must be run on Linux systems.")
        return []

    for dev in os.listdir('/sys/block'):
        # Determine if the device is a physical drive
        if dev.startswith(('loop', 'ram', 'zram', 'md', 'dm-')): continue
        if dev.startswith('sr'): continue

        dev_path = os.path.join('/sys/block', dev)

        if not os.path.exists(os.path.join(dev_path, 'device')): continue

        # Get manufacturer info

        dev_manuf = 'Unknown'
        for name_file in ['device/model', 'device/vendor']:
            full_path = os.path.join(dev_path, name_file)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f: dev_manuf = f.read().strip()
                break

        # Drive device path and capacity
        dev_path = f"/dev/{dev}"
        dev_capac = get_drive_size_raw(dev_path)
        disks.append((dev_path, dev_manuf, dev_capac))

    return disks

def get_drive_size_raw(device):
    device_name = os.path.basename(device)
    sys_path = f"/sys/class/block/{device_name}/size"

    with open(sys_path, 'r') as f: return int(f.read().strip()) * 512

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
