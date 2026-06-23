"""
Clonix: util/constants.py

Flag definitions and systemwide constants; some overridden by config.json
"""

import os

# System constants
# TODO:

# Command input expectations (i.e. confirmations)
YES = 'y\n' * 10

# Partition manager flags
PART_FLAGS = {
        'boot': 0x1,
        'root': 0x2,
        'swap': 0x4,
        'hidden': 0x8,
        'raid': 0x10,
        'lvm': 0x20,
        'lba': 0x40,
        'legacy_boot': 0x80,
        'irst': 0x100,
        'msftres': 0x200,
        'esp': 0x400,
        'chromeos_kernel': 0x800,
        'bls_boot': 0x1000,
        'linux-home': 0x2000,
        'no_automount': 0x4000,
        'bios_grub': 0x8000,
        'palo': 0x10000
}

# First run constants
CLONER_DIR=os.path.join(os.getenv("HOME", ""), "cloner")
TARGET_ROOT="/target"
TARGET_SBIN=os.path.join(TARGET_ROOT, "/usr/local/sbin")
TARGET_SYSTEMD=os.path.join(TARGET_ROOT, "/etc/systemd/system")

TARGET_INIT_SCRIPT=os.path.join(TARGET_SBIN, "init.sh")
TARGET_INIT_SERVICE=os.path.join(TARGET_SYSTEMD, "init.service")

DRIVER_MARKER="# <DRIVER: insert>"
PACKAGE_MARKER="# <PACKAGE: insert>"
