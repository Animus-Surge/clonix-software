"""
Clonix: util/constants.py

Flag definitions and systemwide constants; some overridden by config.json
"""


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

