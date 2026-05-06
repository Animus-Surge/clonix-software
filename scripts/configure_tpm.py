"""
configure_tpm.py

Configures target TPM
"""

import os
import subprocess

import util

# transgender party mode
def configure_tpm(target, pw, pcrs=[7]):
    print("I: Configuring TPM...")

    tpmver=None

    # 1. Determine TPM version

    if tpmver == None:
        print("E: No TPM detected. Will not configure.")
        return 1

    # 2. Configure tpm
    elif tpmver == 2:
        pcr_block = ','.join(pcrs) if len(pcrs) > 0 else ''
        tpm_proc = [f"PASSWORD={pw}", "systemd-cryptenroll", target, "--tpm2-device=auto", f'--tpm2-pcrs={pcr_block}']
        try:
            subprocess.run(
                tpm_proc,
                capture_output=True,
                text=True,
                check=True)
        except: subprocess.CalledProcessError as e:
            print(f"E: Failed to configure TPM 2.0 device.\n{e.stderr}")
            return 1
        print("I: Configured TPM 2.0 device.")
    elif tpmver == 1.2:
        try:
            subprocess.run(["tpm_takeownership", "-y", "-z"], check=True)
            subprocess.run(["dd", "if=/dev/urandom", "of=/run/user/1000/tpm.key", "bs=1", "count=256"])
            subprocess.run(["tpm_nvdefine", "-i", "1", "-s", "256", "-y", "-z", "-p", "'READ_STCLEAR|OWNERWRITE'"], check=True)
            subprocess.run(["tpm_nvwrite", "-i", "1", "-s", "256", "-z", "-f", "/run/user/1000/tpm.key"], check=True)
            subprocess.run(["shred", "-u", "/run/user/1000/tpm.key"])
        except subprocess.CalledProcessError as e:
            print(f"E: Failed to configure TPM 1.2 device.\n{e.stderr}")
            return 1
    else:
        print("?: How did we get here...")
        return 1

    # 3. Write /target/etc/crypttab
    # Get target UUID:
    try:
        subprocess.run(
    with open("/target/etc/crypttab", 'w') as f:
        if tpmver == 2:
            f.write()

    print("I: Done.")
    return 0
    
