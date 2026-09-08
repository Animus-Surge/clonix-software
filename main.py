"""
Clonix - NixOS Python based operating system deployment program

Author: Evan Floyd (Surge)
"""

import argparse
import datetime
import os
import subprocess
import sys

from loguru import logger
import httpx

import deploy
#import freeze

# TODO: other subcommands? i.e. "modify"?

# Argparse configuration
parser = argparse.ArgumentParser(
        prog="clonix",
        description="NixOS/Python based OS cloner")

subparsers = parser.add_subparsers(dest="command", required=True)

deployment_parser = subparsers.add_parser("deploy")
freeze_parser = subparsers.add_parser("freeze")
tui_parser = subparsers.add_parser("tui")

# Positional arguments

# Deployment arguments
deployment_parser.add_argument('source_file')
deployment_parser.add_argument('target')

# Freezing arguments
freeze_parser.add_argument('target_file')

# Flags
parser.add_argument('-D', '--dry-run', action="store_true")

# Deployment flags
deployment_parser.add_argument('-b', '--use-btrfs', action="store_true", help="Use btrfs instead of ext4")
deployment_parser.add_argument('-d', '--dual-boot', action="store_true", help="If the system is dual booted (i.e. for windows)")
deployment_parser.add_argument('-l', '--use-luks', action="store_true", help="Encrypt the root partition")
deployment_parser.add_argument('-m', '--use-tpm', action="store_true", help="Use the TPM as a LUKS key")

# Freezing flags

# Tui flags

# Options
# parser.add_argument('-L', '--log-file') # Removed in favor of default logs in clonix_root/logs
parser.add_argument('-R', '--conf-file')

# Deployment options
deployment_parser.add_argument('-n', '--hostname')
deployment_parser.add_argument('-p', '--package', action="append")
deployment_parser.add_argument('-s', '--subvolume', action="append", help="Format: volname;path;<opts>, where opts appends to mount options.")

# Freezing options
freeze_parser.add_argument('-s', '--source-dir')

# Update checker
def check_update():

    last_etag = None
    update_check_cache_file=os.path.join(os.curdir, 'update_check_last_timestamp')
    if os.path.exists(update_check_cache_file):
        with open(update_check_cache_file, 'r') as f:
            last_etag = f.read().strip()

    headers = {}
    if last_etag:
        headers["If-None-Match"] = last_etag

    try:
        with httpx.Client(follow_redirects = True) as client:
            response = client.head('https://github.com/Animus-Surge/clonix/commits/prod.atom', headers=headers)

            if response.status_code == 304:
                return False
    except httpx.HTTPError as e:
        logger.error("Failed to check update: {}".format(e))
    finally:
        return False

def main(arg_dict: dict):
    # TODO: allow conf-file to override certain values in constants.py; for example
    #       if we have a provisioning system setup such that when a new device is
    #       enrolled into the system it gets enrolled and added to a database, we can
    #       specify that url. It would default to None for portability, but allow
    #       admins to control the behavior of this system.

    # TODO: Additionally, allow a `autodeploy.json` file to be created that would
    #       read the serial number of the system, and use that to determine how to 
    #       provision the system, given the api url. This file would contain an image
    #       name, and determine what to do given the disk layout (which might be able
    #       to be done directly in the api.

    # Subcommand processing
    if arg_dict.get("command"):
        cmd = arg_dict.get("command")

        if cmd == "tui":
            logger.remove()

        logger.add(f"logs/clonix-{datetime.datetime.now()}.log")

        cmdopts = {}

        if cmd == "deploy":
            source = arg_dict.get("source_file")
            target = arg_dict.get("target")

            if not source or not target:
                logger.error("Source or target not given.")
                exit(1)

            # Assemble cmdopts

            if not deploy.deploy():
                # I'm choosing not to print anything here, since the actual system will
                # say something.
                exit(1)
            exit(0)

        elif cmd == "freeze":
            # TODO: implement
            pass

        elif cmd == "tui":
            # TODO: implement
            pass

        elif cmd == "test":
            pass

        else:
            logger.error("Unknown command {}".format(cmd))

    else:
        logger.error("Something went wrong.")
        exit(1)


if __name__ == "__main__":
    # DO THIS FIRST: update checks
    logger.info("Checking for updates...")
    if check_update():
        # Why os.execv? This process changes for updates to take place. update.sh will
        # never change. Passes sys.argv to update.sh, so update.sh can restart this after
        # updating.
        os.execv(os.path.join(os.curdir, 'update.sh'), sys.argv)

    # Checking user ID for elevation
    if os.geteuid() != 0:
        logger.info("Requires root to run.")
        proc = subprocess.run(['sudo', sys.executable] + sys.argv)
        sys.exit(proc.returncode)

    # Make logs dir if not exists
    if not os.path.exists("logs"): os.mkdir("logs")

    args = vars(parser.parse_args())
    main(args)
    
