"""
Clonix: deploy/mk_subvol.py

Creates btrfs subvolumes
"""

import grp
import os
import pwd
import subprocess
import time

from loguru import logger
import psutil

import util

DEFAULT_SUBVOL = [
    { "name": "@", "path": "/", "fs": "btrfs", "opts": "defaults,compress=zstd" },
    { "name": "@home", "path": "/home", "fs": "btrfs", "opts": "defaults,compress=zstd,nodev,nosuid" },
    { "name": "@var", "path": "/var", "fs": "btrfs", "opts": "defaults,compress=zstd,nodev,nosuid" },
    { "name": "@var_log", "path": "/var/log", "fs": "btrfs", "opts": "defaults,compress=zstd,nodev,nexec,nosuid" },
    { "name": "@var_log_audit", "path": "/var/log/audit", "fs": "btrfs", "opts": "defaults,compress=zstd,nodev,noexec,nosuid" },
    { "name": "@var_tmp", "path": "/var/tmp", "fs": "btrfs", "opts": "defaults,compress=zstd,nodev,nosuid" }
]

def mk_subvol(layout = DEFAULT_SUBVOL, encrypted = True, swap = True):

    efi_uuid = None
    boot_uuid = None

    if encrypted:
        efi_uuid = util.get_part_uuid(mountpoint="/target/boot/efi")
        boot_uuid = util.get_part_uuid(mountpoint="/target/boot")
    else:
        efi_uuid = util.get_part_uuid(mountpoint="/target/boot/efi")

    if not efi_uuid: efi_uuid = ""
    if not boot_uuid: boot_uuid = ""

    cwd = os.getcwd()
    os.chdir("/target")

    # Step 1: Create filesystem label(s) and subvolumes
    logger.info("Creating btrfs subvolumes...")

    try:
        subprocess.run(['btrfs', 'filesystem', 'label', '.', 'root'], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        util.log_error(e, "Failed to create filesystem label")
        return False

    if swap:
        layout.append({ "name": "@swap", "path": "/swap", "fs": "btrfs", "opts": "defaults,compress=zstd,nodev,noexec,nosuid" })

    for subvol in layout:
        try:
            cmd = ['btrfs', 'subvolume', 'create', layout.get('name')]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            util.log_error(e, "Failed to create subvolume {}".format(layout.get('name')))
 
        with open("/target/etc/fstab", 'a') as f:
            line = f"LABEL=root {subvol.get('path')} btrfs subvol={subvol.get('name')},{subvol.get('opts')} 0 0"
            f.write(line)

    # Step 2: Copy everything over

    # Unmount efi and stuff
    util.unmount_path("/target/boot/efi")
    util.unmount_path("/target/boot")
    util.unmount_path("/target/dev")
    util.unmount_path("/target/proc")
    util.unmount_path("/target/run")
    util.unmount_path("/target/sys")

    time.sleep(2)
    
    try:
        subprocess.run(["mv", "./var/log/*", "./@var_log"], check=True)
        subprocess.run(["mv", "./var/*", "./@var"], check=True)
        subprocess.run(["mv", "!(@*)", "./@"], check=True)
    except subprocess.CalledProcessError as e:
        pass # TODO

    os.chdir(cwd)

    util.unmount_path("/target", True)

    # Now we re-mount everything

    util.mount_device("LABEL=root", "/target", opts="subvol=@")
    util.mount_device("LABEL=root", "/target/var", opts="subvol=@var")
    util.mount_device("LABEL=root", "/target/var/log", opts="subvol=@var_log")
    time.sleep(1)
    os.mkdir("/target/var/tmp")
    util.mount_device("LABEL=root", "/target/var/tmp", opts="subvol=@var_tmp")

    os.chdir("/target")

    os.mkdir("./var/log/audit")
    os.chown("./var/log/audit", pwd.getpwnam('root').pw_uid, grp.getgrnam('adm').gr_gid)
    os.chmod("./var/log/audit", 750)

    util.mount_device("LABEL=root", "/target/var/log/audit", opts="subvol=@var_log_audit")
    
    if encrypted:
        util.mount_device(os.path.join("/dev/disk/by-uuid", boot_uuid), "/target/boot")
    util.mount_device(os.path.join("/dev/disk/by-uuid", efi_uuid), "/target/boot/efi")

    util.mount_binds("/target")

    # Step 3: Swapfile
    os.mkdir("swap")
    util.mount_device("LABEL=root", "/target/swap", opts="subvol=@swap")

    available_mem = psutil.virtual_memory().available

    try:
        subprocess.run(["btrfs", "filesystem", "mkswapfile", "--size", f"{available_mem}", "--uuid", "clear", "/target/swap/swapfile"], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        util.log_error(e, "Failed to make swapfile.")

    os.chdir(cwd)

    return True
