## CloNIX nontui.py
# Non-tui display option, used when --nogui is given to the program, or `config.json` contains
# "notui": true

# Literally a python implementation of ./cloner_bash/deploy.sh

import os
import subprocess

import util

m_source = None
m_target = None

m_hostname = None
m_is_dual_boot = None

m_use_btrfs = None
m_use_btrfs_compress_alg = 'zstd'
m_use_luks = None
m_use_log_file = None
m_use_tpm = None
m_tpm_version = util.get_tpm_version()

# Sets the non-tpm options; used for prompting where necessary and storing values
def set_options(source, target, set_hostname):
    global m_source, m_target, m_hostname, m_is_dual_boot, m_use_btrfs, m_use_btrfs_compress_alg
    global m_use_luks, m_use_log_file, m_use_tpm

    m_source = source
    m_target = target
    
    m_hostname = set_hostname

def run():
    print("INFO: Using non-tui version.")

    global m_source, m_target, m_hostname, m_is_dual_boot, m_use_btrfs
    global m_use_btrfs_compress_alg, m_use_luks, m_use_log_file, m_use_tpm
    if m_source == None:
        print("No source image. Enter the absolute path of the source image")
        m_source = input("> ")
        while not os.path.exists(m_source):
            print("Enter the absolute path of the source image")
            m_source = input("> ")

    if m_target == None:
        print("No target. Enter the device path of the target disk (i.e. /dev/sda)")
        m_target = input("> ")
        while not os.path.exists(m_target):
            print("Enter the device path of the target disk (i.e. /dev/sda)")
            m_target = input("> ")

    if m_hostname == None:
        print("No hostname. Enter target hostname")
        m_hostname = input("> ")

    if m_use_luks == None:
        use_luks = input("Use LUKS encryption? (Y/n) > ")
        if len(use_luks) == 0 or use_luks.lower()[0] == 'y':
            m_use_luks = True
        else:
            m_use_luks = False

    if m_use_tpm == None:
        use_tpm = input("Use TPM encryption? (Y/n) > ")
        if len(use_tpm) == 0 or use_tpm.lower()[0] == 'y':
            m_use_tpm = True
            m_use_luks = True  # use_luks is ALWAYS true when using tpm
        else:
            m_use_tpm = False

    if m_use_btrfs == None:
        use_btrfs = input("Use btrfs filesystem? (y/N) > ")
        if len(use_tpm) == 0 or use_tpm.lower()[0] == 'n':
            m_use_btrfs = False
        else:
            m_use_btrfs = True

            if m_use_btrfs_compress_alg == None:
                btrfs_alg = input("Enter compression algorthm (default zstd) > ")
                # TODO: checking

                if len(btrfs_alg) == 0:
                    m_use_btrfs_compress_alg = "zstd"
                else:
                    m_use_btrfs_compress_alg = btrfs_alg

    print( "")
    print( "=== SUMMARY ===")
    print(f"Source file: {m_source}")
    print(f"Target disk: {m_target}")
    print(f"Target hostname: {m_hostname}")
    print(f"Use LUKS encryption: {m_use_luks}")
    print(f"Use TPM encryption: {m_use_tpm}")
    print(f"Use btrfs: {m_use_btrfs}")

    # TODO: dual boot stuff (i don't wanna deal with them right now)
    # TODO: the btrfs stuff too

    print("")
    print("WARNING: Once started, this process is IRREVERSABLE! Make sure")
    print("         to back up any and ALL data that you might need!")

    print("")
    confirmation = input("Are you sure you would like to begin? (y/N) > ")

    if len(confirmation) == 0 or confirmation.lower()[0] == 'n':
        print("WARNING: Abort.")
        exit(1)
        return

    print("INFO: Starting deployment.")
    subprocess.run(["./scripts/format_boot_encrypted.sh"], shell=True)



