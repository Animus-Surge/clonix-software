"""
Clonix: deploy/setup.py

Initial setups and chroots
"""

import os
import shlex
import subprocess

from loguru import logger

import util
from util import constants
from util import globals

def setup_image() -> bool:
    logger.info("Setting up initrd...")

    kver = ""

    try:
        entries = os.listdir("/target/lib/modules")
        dirs = sorted([e for e in entries if os.path.isdir(os.path.join("/target/lib/modules", e))])
        kver = dirs[0] if dirs else ""
    except FileNotFoundError:
        return False

    if kver == "": 
        logger.error("Failed to get kernel version. Maybe copying failed?")
        return False

    try:
        subprocess.run(["chroot", "/target", "/bin/bash", "apt-get", "update"], check=True)
        subprocess.run(["chroot", "/target", "/bin/bash", "apt-get", "reinstall", f"linux-image-{kver}", f"linux-modules-{kver}", f"linux-modules-extra-{kver}"], check=True)
    except subprocess.CalledProcessError as e:
        util.log_error(e, "Failed to reinstall linux-image and linux-modules.")
        return False
    
    logger.success("Reinstalled initrd.")
    return True

def setup_do_upgrades() -> bool:
    logger.info("Doing system upgrades...")

    return util.run_chroot_process("apt-get upgrade")

def setup_grub() -> bool:
    logger.info("Setting up grub...")

    try:
        subprocess.run(["chroot", "/target", "/bin/bash", "grub-install", "--target=x86_64-efi", "--efi-directory=/boot/efi", "--bootloader-id=ubuntu", "--recheck"], check=True)
        subprocess.run(["chroot", "/target", "/bin/bash", "grub-mkconfig", "-o", "/boot/efi/EFI/ubuntu/grub.cfg"], check=True)
    except subprocess.CalledProcessError as e:
        util.log_error(e, "Failed to reinstall grub.")
        return False

    logger.success("Reinstalled grub.")
    return True

def setup_crypt(target: str, psp: str, partnum_override=3, use_tpm=True) -> bool:
    logger.info("Configuring encryption options...")

    with open("/target/etc/crypttab", 'w') as f:
        f.write("# <target name> <source device>     <key file>  <options>\n")

    crypt_uuid = ""
    prefix = "p" if "nvme" in target else ""
    cmd = ["cryptsetup", "luksUUID", f"{target}{prefix}3"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    if result.returncode == 0:
        crypt_uuid = result.stdout.strip()

    if use_tpm and os.path.exists("/dev/tpm0"):
        # TPM present

        # TODO: PCR handling
        if os.path.exists("/dev/tpmrm0"):
            # TPM 2.0
            try:
                subprocess.run(shlex.split("chroot /target /bin/bash apt-get install -y tpm2-tools"), check=True, capture_output=True, text=True)
                subprocess.run(shlex.split(f'PASSWORD="{psp}" chroot /target /bin/bash systemd-cryptenroll {target}{prefix}{partnum_override} --tpm2-device=auto'), check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                util.log_error(e, "Failed to setup TPM 2.0 cryptsetup options.")
                return False
            

            with open("/target/etc/crypttab", 'a') as f:
                f.write(f"dm_crypt-0 {crypt_uuid} none luks,tpm2-device=auto")

            with open("/target/etc/dracut.conf.d/10-encrypt.conf", "w") as f:
                f.write('omit_dracutmodules+=" tpm12 "')

            logger.success("Configured TPM 2.0 encryption.")
        else:
            # TPM 1.2
            globals.COPY_TPM_12_DRACUT_MODULE = True

            if not util.run_chroot_process("apt-get install -y trousers tpm-tools"): return False
            if not util.run_chroot_process("tpm_takeownership -y -z"): return False
            if not util.run_chroot_process("dd if=/dev/urandom of=/run/user/1000/tpm.key bs=1 count=256"): return False
            if not util.run_chroot_process("tpm_nvdefine -i 1 -s 256 -y -z -p 'READ_STCLEAR|OWNERWRITE' -r 7"): return False
            if not util.run_chroot_process("tpm_nvwrite -i 1 -s 256 -f /run/user/1000/tpm.key -z"): return False
            if not util.run_chroot_process(f"cryptsetup luksAddKey {target}{prefix}{partnum_override} /run/user/1000/tpm.key", user_input=psp): return False
            util.run_chroot_process("shred -u /run/user/1000/tpm.key")

            with open("/target/etc/crypttab", 'a') as f:
                f.write(f"dm_crypt-0 {crypt_uuid} /mnt/tpm/key luks")

            with open("/target/etc/dracut.conf.d/10-encrypt.conf", "w") as f:
                f.write('omit_dracutmodules+=" tpm2-tss "')

            logger.success("Configured TPM 1.2 Encryption.")
    else:
        if use_tpm:
            logger.info("No TPM detected. Defaulting to standard LUKS encryption.")
        else:
            logger.info("Configuring standard LUKS encryption...")

        with open("/target/etc/crypttab", 'a') as f:
            f.write(f"dm_crypt-0 {crypt_uuid} none luks")

    # Master key QR code handled in main file
    logger.success("Configured encryption settings.")

    return True

