"""
Clonix: deploy/setup.py

Initial setups and chroots
"""

import os
import subprocess

from loguru import logger

import util
from util import constants
from util import qr

def setup_image():
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

def setup_grub():
    logger.info("Setting up grub...")

    try:
        subprocess.run(["chroot", "/target", "/bin/bash", "grub-install", "--target=x86_64-efi", "--efi-directory=/boot/efi", "--bootloader-id=ubuntu", "--recheck"], check=True)
        subprocess.run(["chroot", "/target", "/bin/bash", "grub-mkconfig", "-o", "/boot/efi/EFI/ubuntu/grub.cfg"], check=True)
    except subprocess.CalledProcessError as e:
        util.log_error(e, "Failed to reinstall grub.")
        return False

    logger.success("Reinstalled grub.")
    return True

def setup_crypt(target: str, psp: str):
    logger.info("Configuring encryption options...")

    with open("/target/etc/crypttab", 'w') as f:
        f.write("# <target name> <source device>     <key file>  <options>\n")


    if os.path.exists("/dev/tpm0"):
        if os.path.exists("/dev/tpmrm0"):
            # TPM 2.0
            try:
                subprocess.run(["chroot", "/target", "/bin/bash", "apt-get", "install", "tpm2-tools"], input=constants.YES, check=True)
                subprocess.run([f"PASSWORD={psp}", "chroot", "/target", "/bin/bash", "systemd-cryptenroll", "/dev/mapper/dm_crypt-0", "--tpm2-device=auto"], check=True)
            except subprocess.CalledProcessError as e:
                util.log_error(e, "Failed to setup TPM 2.0 cryptsetup options.")
                return False
            
            crypt_uuid = ""
            prefix = "p" if "nvme" in target else ""
            cmd = ["cryptsetup", "luksUUID", f"{target}{prefix}3"]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            if result.returncode == 0:
                crypt_uuid = result.stdout.strip()

            with open("/target/etc/crypttab", 'a') as f:
                f.write(f"dm_crypt-0 {crypt_uuid} none luks,tpm2-device=auto")

            with open("/target/etc/dracut.conf.d/10-encrypt.conf", "w") as f:
                f.write('omit_dracutmodules+=" tpm12 "')

            logger.success("Configured TPM 2.0 encryption.")
        else:
            # TODO: TPM 1.2
            pass
    else:
        logger.info("No TPM detected. Defaulting to standard LUKS encryption.")
        # TODO: luks

    # Here's where we will generate the QR code for the master LUKS key
    
    logger.info("Grabbing master key...")
    # TODO: master key
    pass

