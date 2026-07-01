"""
Clonix: util/globals.py

Global variables and things to be transferred between different threads
"""

# Status flags
from util.partman import Partman

COPY_PROGRESS = 0
STATE = 0

# Flags
IN_TUI = False
DRY_RUN = False
COPY_TPM_12_DRACUT_MODULE = False

# State machine

partman_inst = None
def get_partman_inst():
    global partman_inst
    if not partman_inst:
        partman_inst = Partman()
    return partman_inst
