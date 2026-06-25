"""
Clonix: deploy/__init__.py

Deployment processes
"""

import os
import shutil
import subprocess

from deploy.subvolumes import mk_subvol
from deploy.first_run import generate_init

import util
from util import globals
from util import qr

from deploy.partition import *
from deploy.setups import *
from loguru import logger

def start_deployment(source, target, opts: dict = {}, psp: str | None = None):
    # Initial checks
    if not os.path.exists(source) or not os.path.exists(target):
        logger.critical("Given source or target does not exist.")
        return False
    
    if not psp and opts.get('luks', False):
        logger.critical("Encrypted systems must include a passphrase.")
        return False

    """
    opts (Flags default True, subvols default []):

    {
      'hostname': <str>,
      'btrfs': <bool>,
      'btrfs_defaults': <bool>,
      'btrfs_subvols': <list>,
      'luks': <bool>,
      'tpm': <bool>,
      'swap': <bool>,
      'post_install': <dict>
    }

    post_install
    {
      'create_init': <bool>,
      'reset_puppet_config': <bool>
    """

    # Set flags
    use_luks = opts.get("luks", True)
    use_tpm = opts.get("tpm", True)
    use_btrfs = opts.get("btrfs", True)
    use_swap = opts.get("swap", True)
    use_btrfs_defaults = opts.get("btrfs_defaults", True)
    btrfs_subvols = opts.get("btrfs_subvols", [])

    logger.info(f"Starting deployment on {target}. Using {source}...")
    logger.info(f"Use btrfs: {use_btrfs}")
    logger.info(f"btrfs default subvolumes: {use_btrfs_defaults}")
    # TODO: custom subvolume layouts
    logger.info(f"Use luks: {use_luks}")
    logger.info(f"Use swap: {use_swap}")
    logger.info(f"Use tpm: {use_tpm}")

    logger.info("1: Format target...")

def deploy_encrypted_standard(source, target, psp, opts):
    prefix = "p" if "nvme" in target else ""

    # Partition
    if not mk_parts([target], 0, psp):
        logger.critical("Failed to format target.")
        return False

    # Mount
    efi_uuid = util.get_part_uuid(device=f"{target}{prefix}1")
    boot_uuid = util.get_part_uuid(device=f"{target}{prefix}2")
    root_id = util.get_part_uuid(device=f"/dev/mapper/dm_crypt-0", by_id=True)

    if not util.mount_device("/dev/mapper/dm_crypt-0", "/target"): return False
    
    # Copy
    logger.info("Copying source to /target...")
    
    pzstd = [shutil.which('pzstd'), '-dcq', source]
    tar = ['tar', '--xattrs', '--xattrs-include=*', '-xpf', '-', '-C', '/target']

    pzstd_proc = subprocess.Popen(pzstd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    tar_proc = subprocess.Popen(tar, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    try:
        chunk_size = 1024 * 1024
        while True:
            chunk = pzstd_proc.stdout.read(chunk_size)
            if not chunk: break

            tar_proc.stdin.write(chunk)
            globals.COPY_PROGRESS += len(chunk)

    finally:
        pzstd_proc.stdout.close()
        tar_proc.stdin.close()

        pzstd_proc.wait()
        tar_proc.wait()

    if tar_proc.returncode != 0:
        logger.error(f"tar extraction failed. Exit code: {tar_proc.returncode}")
        return False
    logger.success("Copied base image to /target.")

    # Mount extras
    if not util.mount_device(f"/dev/disk/by-uuid/{boot_uuid}", "/target/boot"): return False
    if not util.mount_device(f"/dev/disk/by-uuid/{efi_uuid}", "/target/boot/efi"): return False

    if not util.mount_binds("/target"): return False

    # Btrfs
    if not mk_subvol(): return False

    # Setup
    if not setup_image(): return False
    if not setup_do_upgrades(): return False
    if not setup_grub(): return False
    if psp:
        if not setup_crypt(target, psp): return False

    try:
        entries = os.listdir("/target/lib/modules")
        dirs = sorted([e for e in entries if os.path.isdir(os.path.join("/target/lib/modules", e))])
        kver = dirs[0] if dirs else ""
    except FileNotFoundError:
        return False

    with open("/target/etc/hostname", 'w') as f:
        f.write(opts.get("hostname", ""))

    try:
        subprocess.run(["chroot", "/target", "/bin/bash", "dracut", "-f", "--kver" if kver else "", kver if kver else ""], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        util.log_error(e, "Failed to generate final initrd.")
        return False

    # init.sh generation
    if not generate_init(psp):
        logger.error("Failed to generate init.sh files.")

    logger.success("Completed install step.")
    
    # Post-install steps; non-critical. Anything that fails here will not cause a failed install.

    # Grab master volume key
    try:
        subprocess.run(["cryptsetup", "luksDump", "--dump-master-key", "--master-key-file", "/run/user/1000/keyfile.bin", target], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        util.log_error(e, "Failed to grab master LUKS key. You may need to do this manually.")
    finally:
        if os.path.exists("/run/user/1000/keyfile.bin"):
            with open("/run/user/1000/keyfile.bin", 'rb') as f:
                key = f.read().hex()
                logger.info("Scan this QR code to get the master LUKS key.")
                code = qr.generate_copy_qr(key)
                print(code)
            subprocess.run(["shred", "-u", "/run/user/1000/keyfile.bin"])

    # Compress filesystem
    if not util.btrfs_defragment("/target"):
        logger.error("Failed to compress filesystem. You may need to do this manually.")



    # Done
    logger.success("Completed deployment.")

    return True

