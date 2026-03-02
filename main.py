from __future__ import annotations

import argparse
import os
import signal

import tui
import util

"""
TODO BOARD

- Logging
- Non-TUI; prompt/option based setup
- Bash script creation for steps
"""

# Argument setup
parser = argparse.ArgumentParser(
        prog='CloNIX',
        description='NixOS/Filesystem based OS cloner')

parser.add_argument('-C', '--config', help='Use this specific config file') # Load specific config file

# Following options are here parallel for the existing bash script
parser.add_argument('-f', '--source', help='Define the source file; will prompt if omitted')
parser.add_argument('-t', '--target', help='Define the target disk; will prompt if omitted')

parser.add_argument('-b', '--btrfs', help='Whether to use btrfs instead of ext4', action='store_true', default=False)
parser.add_argument('-c', '--compress', help='Used with btrfs; defines the compression method (default zstd)', default='zstd')
parser.add_argument('-d', '--dual-boot', help='Whether or not the system is dual booted', action='store_true', default=False)
# Omitting dry-run option
parser.add_argument('-l', '--luks', help='Use LUKS[2] encryption (default true)', action='store_true', default=True)
parser.add_argument('-L', '--log-file', help='Log file to output to') # TODO: implement logging
parser.add_argument('-m', '--tpm', help='Use the TPM for encryption (enables LUKS) (default true)', action='store_true')
parser.add_argument('-n', '--hostname', help='Defines the hostname of the target system (default invalid)')
# Omitting package, property, conf-file

parser.add_argument('-T', '--no-tui', help='Disables the TUI') # Disables TUI 


def signal_handler(sig, frame):
    if sig == signal.SIGINT: # Stop ctrl+c raising KeyboardInterrupt
        raise urwid.ExitMainLoop()
    pass

# Main stuff below here
def init():
    args = vars(parser.parse_args())
    util.load_config(args.get('config'))
    signal.signal(signal.SIGINT, signal_handler)

    if args.get('disable-tui'):
        pass
    else:
        tui.TUIController().run()

if __name__=="__main__":
    print("Loading...") # If this gets printed, THE PROGRAM WORKS
    init()

