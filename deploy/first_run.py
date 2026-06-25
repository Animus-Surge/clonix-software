"""
Python implementation of create_first_run

Generates the first run script
"""

import json
import os
import re
import subprocess
import sys

from loguru import logger

import util
from util import constants

# Default configuration
DEFAULT_CONFIG={
    "NVIDIA_DRIVER_DEFAULT_VERSION": 580,
    "NVIDIA_DRIVER_DO_INSTALL": True,
    "LABVIEW_DRIVERS_DO_INSTALL": False
}

# Markers
DRIVER_MARKER="# <DRIVER: insert>"
PACKAGE_MARKER="# <PACKAGE: insert>"
SNIPPET_DIR=os.path.join(constants.CLONER_DIR, "snippets")

config=DEFAULT_CONFIG

def insert_snippet(marker, replacement_file):
    logger.info("Copying {} to {}".format(replacement_file, constants.TARGET_INIT_SCRIPT))
    
    with open(replacement_file, 'r') as f:
        snippet_content = f.read()

    with open(constants.TARGET_INIT_SCRIPT, 'r') as f:
        target_lines = f.readlines()

    output_lines=[]

    for line in target_lines:
        output_lines.append(line)
        if line.rstrip('\r\n') == marker:
            if not snippet_content.endswith('\n'):
                output_lines.append(snippet_content + '\n')
            else:
                output_lines.append(snippet_content)

    with open(constants.TARGET_INIT_SCRIPT, 'w') as f:
        f.writelines(output_lines)

def insert_snippet_placeholder(marker, replacement_file, placeholder, placeholder_replacement, redact_placeholder=False):
    logger.info("Copying {} to {}; replacing {} with {}".format(replacement_file, constants.TARGET_INIT_SCRIPT, placeholder, placeholder_replacement if not redact_placeholder else "[HIDDEN]"))
    with open(replacement_file, 'r') as f:
        snippet_content = f.read()

    updated_snippet=re.sub(re.escape(placeholder), str(placeholder_replacement), snippet_content)

    with open(constants.TARGET_INIT_SCRIPT, 'r') as f:
        target_lines = f.readlines()

    output_lines=[]

    for line in target_lines:
        output_lines.append(line)
        if line.rstrip('\r\n') == marker:
            if not updated_snippet.endswith('\n'):
                output_lines.append(updated_snippet + '\n')
            else:
                output_lines.append(updated_snippet)

    with open(constants.TARGET_INIT_SCRIPT, 'w') as f:
        f.writelines(output_lines)

def copy_file(source, target):
    # WARNING: this function overwrites the target completely!
    if os.path.exists(target):
        os.remove(target)

    with open(source, "r") as f:
        source_content = f.read()

    with open(target, "w") as f:
        f.write(source_content)

    logger.info("Copied {} to {}".format(source, target))

def copy_file_placeholder(source, target, placeholder, replacement, redact_placeholder=False):
    # WARNING: this function overwrites the target completely!
    if os.path.exists(target):
        os.remove(target)

    with open(source, "r") as f:
        source_content = f.read()

    replaced_source_content = re.sub(re.escape(placeholder), replacement, source_content)

    with open(target, "w") as f:
        f.write(replaced_source_content)

    logger.info("Copied {} to {}; replaced {} with {}".format(source, target, placeholder, replacement if not redact_placeholder else "[HIDDEN]"))


def generate_init(mok_pw):
    global config
    
    if len(sys.argv) >= 2 and sys.argv[1] and os.path.exists(sys.argv[1]):
        with open(os.path.abspath(sys.argv[1]), 'r') as f:
            logger.info("Using config file {}".format(sys.argv[1]))
            config = json.loads(f.read())

    logger.info("Creating first run script and service...")

    # Arguments
    if not mok_pw:
        # Non-critical error, will not quit.
        logger.error("No cloner password set; will not be able to handle MOK.")

    # Other dirs should exist already

    # Create init.service
    copy_file(os.path.join(SNIPPET_DIR, "init.service.snip"), constants.TARGET_INIT_SERVICE)
    
    # Create init.sh
    copy_file_placeholder(os.path.join(SNIPPET_DIR, "init.sh.snip"), constants.TARGET_INIT_SCRIPT, "<replaceme>", mok_pw, True)

    # Drivers
    if config.get("NVIDIA_DRIVER_DO_INSTALL"):
        version = config.get("NVIDIA_DRIVER_DEFAULT_VERSION", 580)
        insert_snippet_placeholder(constants.DRIVER_MARKER, os.path.join(SNIPPET_DIR, "NVIDIA_DRIVER_INSTALL.sh.snip"), "<NVIDIA_DRIVER_DEFAULT_VERSION>", version)

    if config.get("LABVIEW_DRIVERS_DO_INSTALL"):
        insert_snippet(constants.DRIVER_MARKER, os.path.join(SNIPPET_DIR, "INSTALL_LABVIEW_DRIVERS.sh.snip"))

    # Packages
    # Nothing here yet.

    # Activate the service
    try:
        subprocess.run(["/bin/systemctl", "--root=/target", "enable", "init.service"], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        log_error(e, f"Failed to enable init.service.")
        return False

    logger.success("Created and enabled init service.")
    return True

