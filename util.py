"""
egr-cloner util.py

Utility functions
"""

import json
import os
import subprocess

MASTER_PALETTE = [
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

        # Popups
        ('popup-error', 'light red', 'black', 'bold', '#f00', '#333'),
        ('popup-warning', 'yellow', 'black', 'bold', '#ff0', '#333'),
        ('popup-success', 'light green', 'black', 'bold', '#7f7', '#333'),
        ('popup-regular', 'white', 'black', 'default', '#fff', '#333')
        #('button-disabled'),
        #('button-selected'),
        #('button-danger'),
]


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

# Icons
# Not implemented.

config = {
    "title_text": "Linux Deployment System"
}

# TTY?
def get_tty():
    return os.ttyname(1).split('/')[-1]

# Configuration handling
def get_config(key: str):
    return config.get(key, '')

def load_config():
    global config
    try:
        with open("./config.json", "r") as f:
            config = config | json.load(f)
    except:
        pass # Ignore

# Devices and stuff
def get_disks():
    cmd = ['lsblk', '-d', '-J', '-o', 'NAME,SIZE,MODEL']
    result = subprocess.run(cmd, capture_output=True, text=True)

    data = json.loads(result.stdout)
    disks = []
    for device in data['blockdevices']:
        disks.append({ "device": f"/dev/{device['name']}", "capacity": device['size'], "model": device['model']})

    return disks

def get_disk_capacity(disk):
    device = disk.split('/')[-1]
    path = f"/sys/block/{device}/size"

    if not os.path.exists(path): raise FileNotFoundError("Failed to determine block size for {device}")

    with open(path, 'r') as f:
        total_bytes = int(f.read().strip()) * 512
        return total_bytes / (1024**3)

def calculate_partition_table(disk, partitions):
    total_capacity = get_disk_capacity(disk)
    output = []

    allocated = sum(p[1] for p in partitions if p[1] != -1)

    for num, size, fstype, mount in partitions:
        actual = 0
        if size == -1:
            actual = max(0, total_capacity - allocated)
        else:
            actual = size

        size_str = f"{actual:.2}G"
        output.append(f"- {num} {fstype} {size_str} {mount}")

    return output

if __name__=="__main__":
    print(get_disks())
