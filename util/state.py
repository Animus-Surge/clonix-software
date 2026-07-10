"""
Clonix: util/state.py

State and singleton handling
"""

import util.partman as partman

partman_inst = None
def get_partman_inst() -> partman.Partman:
    global partman_inst
    if not partman_inst:
        partman_inst = partman.Partman()
    return partman_inst
