"""
egr-cloner util.py

Utility functions
"""

import json
import math
import os
import subprocess

# Constants
VERSION = "v0.3.0"
MASTER_PALETTE = [  # urwid palette

        # Text
        ('text-title', 'white', 'black', 'bold'),
        ('text-normal', 'light gray', 'black', 'default'),
        ('text-error', 'light red', 'black', 'bold'),
        ('text-warning', 'yellow', 'black', 'bold'),
        ('text-success', 'light green', 'black', 'bold'),

        # Input extras
        ('button-highlight', 'light cyan', 'black', 'default'),
        ('button-regular', 'white', 'black', 'default'),

        ('edit-highlight', 'black', 'light cyan', 'bold'),
        ('edit-error', 'black', 'light red', 'bold'),
        ('edit-success', 'black', 'light green', 'bold'),
        ('edit-regular', 'black', 'light gray', 'default'),
        ('edit-disabled', 'black', 'dark gray', 'strikethrough'),

        # Progress bar ; TODO: fix
        ('prog-normal', 'white', 'black', 'default'),
        ('prog-fill', 'black', 'light cyan', 'default'),

        # Popups
        ('popup-error', 'light red', 'black', 'bold', '#f00', '#333'),
        ('popup-warning', 'yellow', 'black', 'bold', '#ff0', '#333'),
        ('popup-success', 'light green', 'black', 'bold', '#7f7', '#333'),
        ('popup-regular', 'white', 'black', 'default', '#fff', '#333')
        #('button-disabled'),
        #('button-selected'),
        #('button-danger'),
]


# NVIDIA driver specific options
# idea is to scan the GPU in the system, and if it's a particular GPU we install a particular version,
# otherwise install 580
NVIDIA_DRIVER_DEFAULT_VERSION = 580

# Characters

# Check boxes
CHK_UNCHECKED = '\u25a1'
CHK_CHECKED = '\u25a0'

# Arrows
ARROW_UP = '\u25b2'
ARROW_DOWN = '\u25bc'
ARROW_LEFT = '\u25c0'
ARROW_RIGHT = '\u25b6'

# Radio buttons
RADIO_UNSELECTED = '\u25cb'
RADIO_SELECTED = '\u25cf'
RADIO_DOT = '\u2299'

# Blocks (progress)
BOX_FULL = '\u2588'
BOX_DARK = '\u2593'
BOX_MED = '\u2592'
BOX_LIGHT = '\u2591'

# Lines
LINE_SINGLE_VERTICAL = '\u2502'
LINE_SINGLE_HORIZONTAL = '\u2500'

LINE_DOUBLE_VERTICAL = '\u2551'
LINE_DOUBLE_HORIZONTAL = '\u2550'

CORNER_SINGLE_TOP_RIGHT = '\u2510'
CORNER_SINGLE_TOP_LEFT = '\u250c'
CORNER_SINGLE_BOTTOM_RIGHT = '\u2518'
CORNER_SINGLE_BOTTOM_LEFT = '\u2514'

CORNER_DOUBLE_TOP_RIGHT = '\u2557'
CORNER_DOUBLE_TOP_LEFT = '\u2554'
CORNER_DOUBLE_BOTTOM_RIGHT = '\u255d'
CORNER_DOUBLE_BOTTOM_LEFT = '\u255a'

CORNER_ROUND_TOP_RIGHT = '\u256e'
CORNER_ROUND_TOP_LEFT = '\u256d'
CORNER_ROUND_BOTTOM_RIGHT = '\u256f'
CORNER_ROUND_BOTTOM_LEFT = '\u2570'

T_SINGLE_UP = '\u2534'
T_SINGLE_DOWN = '\u252c'
T_SINGLE_LEFT = '\u2524'
T_SINGLE_RIGHT = '\u251c'

T_DOUBLE_UP = '\u2569'
T_DOUBLE_DOWN = '\u2566'
T_DOUBLE_LEFT = '\u2563'
T_DOUBLE_RIGHT = '\u2560'

CROSS_SINGLE = '\u253c'
CROSS_DOUBLE = '\u256c'

LINE_CAP_THIN_LEFT = '\u2576'
LINE_CAP_THIN_RIGHT = '\u2574'
LINE_CAP_THIN_TOP = '\u2577'
LINE_CAP_THIN_BOTTOM = '\u2575'

LINE_CAP_THICK_LEFT = '\u257a'
LINE_CAP_THICK_RIGHT = '\u2578'
LINE_CAP_THICK_TOP = '\u257b'
LINE_CAP_THICK_BOTTOM = '\u2579'

ICON_FILE = '\uea7b'
ICON_DIRECTORY = '\uea83'
ICON_RUN = '\ueb9e'
ICON_WARNING = '\uea6c'
ICON_ERROR = '\uea87'

# Default configuration

config = {
    "title_text": "Linux Deployment System"
}


# Configuration handling
def get_config(key: str):
    return config.get(key, '')

def load_config(path="./config.json"):
    global config
    if path is None: path = './config.json'
    try:
        with open(path, "r") as f:
            config = config | json.load(f)
    except:
        pass


# Data handling (TODO: requests)
def get_data(key):
    pass

def load_data_from_remote():
    server = get_config("server")
    if server:
        pass # TODO: a backend for this?
    else:
        pass

def load_data_from_file(path):
    try:
        with open(path, 'r') as f:
            pass
    except:
        pass


# Pretty printing and stuff
def bytes_to_human_readable(byte_in):
    if byte_in == 0: return "0B"

    units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")

    i = int(math.floor(math.log(byte_in, 1000)))

    p = math.pow(1000, i)
    s = round(byte_in/p, 2)

    return f"{s}{units[i]}"


# Devices and stuff

def get_disks():
    cmd = ['lsblk', '-d', '-J', '-o', 'NAME,SIZE,MODEL']
    result = subprocess.run(cmd, capture_output=True, text=True)

    data = json.loads(result.stdout)
    disks = []
    for device in data['blockdevices']:
        disks.append({ "device": f"/dev/{device['name']}", "capacity": device['size'], "model": device['model']})

    return disks

# Get a partition's UUID, given the device path (e.g. /dev/sda1 -> 12345678-9abc-def0-12345678)
def get_part_uuid(path):
    try:
        result = subprocess.check_output(['blkid', '-s', 'UUID', '-o', 'value', path], stderr=subprocess.STDOUT, check=True)
        return result.strip()
    except subprocess.CalledProcessError:
        return None
    except FileNotFoundError:
        print("E: 'blkid' command not found.") # TODO: override print function to allow it to work with or without TUI mode
        return None

# Returns the current TPM version
def get_tpm_version():
    if os.path.exists("/dev/tpm0"):
        if os.path.exists("/dev/tpmrm0"):
            return "2.0"
        else:
            return "1.2"
    else:
        return None


# PCI bus operations

NVIDIA_PCIE_VENDOR_ID = '10de'

# Determine if and what nvidia gpu is installed
def determine_nvidia_version():
    # Blackwell gpus: 10de:2(cde)xx
    pattern = re.compile(r'10de:(2c|2d|2e)[0-9a-f]{2}', re.IGNORECASE)

    try:
        lspci_output = subprocess.check_output(['lspci', '-nn'], text=True)
        gpu_found = False
        is_blackwell = False

        for line in lspci_output.splitlines():
            if NVIDIA_PCIE_VENDOR_ID in line.lower() and "VGA" in line:
                gpu_found = True

                if pattern.search(line):
                    is_blackwell = True # All done
                    break

        if not gpu_found: return None

        if is_blackwell:
            return 590
        else:
            return 580

    except FileNotFoundError:
        print("E: 'lspci' command not found.")
    except Exception as e:
        print("E: Error occured: {e}")

    return None # No GPU

