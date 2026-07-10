"""
Clonix: util/constants.py

Flag definitions and systemwide constants; some overridden by config.json
"""

import os

# System constants
CLONIX_VERSION = "v2.4"
CLONIX_TITLE = "Clonix"
# MUST GET OVERRIDDEN FOR PRODUCTION ENVIRONMENTS
CLONIX_API_URL = "localhost:5000"

# System flags
DRY_RUN = True  # Whether critical operations should be executed or not
DEVELOP_MODE = True # Handles if dev mode variable checking should take place. Also controls log state
LOG_STATE = 'vvv'  # Handled by the -v/--verbose options

# Command input expectations (i.e. confirmations)
YES = 'y\n' * 10

# First run constants
CLONER_DIR=os.path.join(os.getenv("HOME", ""), "cloner")
TARGET_ROOT="/target"
TARGET_SBIN=os.path.join(TARGET_ROOT, "/usr/local/sbin")
TARGET_SYSTEMD=os.path.join(TARGET_ROOT, "/etc/systemd/system")

TARGET_INIT_SCRIPT=os.path.join(TARGET_SBIN, "init.sh")
TARGET_INIT_SERVICE=os.path.join(TARGET_SYSTEMD, "init.service")

DRIVER_MARKER="# <DRIVER: insert>"
PACKAGE_MARKER="# <PACKAGE: insert>"

# Utilities
BYTE_MULTIPLIERS = {
    'K': 1024,
    'M': 1024**2,
    'G': 1024**3,
    'T': 1024**4,
    'E': 1024**5,
}

# TUI characters

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
