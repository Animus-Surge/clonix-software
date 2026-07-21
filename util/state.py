"""
Clonix: util/state.py

State and singleton handling
"""

import util.partman as partman

from util import load_system_data

partman_inst = None
def get_partman_inst() -> partman.Partman:
    global partman_inst
    if not partman_inst:
        partman_inst = partman.Partman()
    return partman_inst


system_data = {}
def get_system_data() -> dict:
    global system_data
    if system_data == None:
        system_data = load_system_data()
    return system_data
