"""
Clonix: freeze/__init__.py

Image freeze and metadata generation
"""

import os
import shutil
import subprocess

import httpx
from loguru import logger

import gen_metadata
from util import log_error
from util.constants import *

from . import commands

def start_freeze(source: str, image_name_prepend: str = "", to_file = False, progress_callback: function | None = None):
    # Gather information for metadata
    source_usage = shutil.disk_usage(source).used
    metadata = gen_metadata.generate(source, source_usage)

    # Check for required and optional binaries
    if not os.path.exists("/usr/bin/tar") or not os.path.exists("/usr/bin/pzstd"):
        return False

    if to_file:
        os.mkdir(CLONIX_LOCAL_IMAGE_DIR)

    # Commands
    excludes = [
        "dev/*",
        "proc/*",
        "run/*",
        "sys/*",
        "tmp/*",
        "home/*",
        "var/cache/apt/*",
        "var/log/journal/*", # NEW: prevent old journals from appearing, since they have a different UUID
        "etc/puppetlabs/puppet/ssl",
        "etc/ssh/ssh_host_*",
    ]

    tar_cmd = [
        "tar",
        "--create",
        "--file=-",
        "--absolute-names",
        "--preserve-permissions",
        "--sparse",
        "--xattrs",
        "--xattrs-include=*",
        "--acls",
        "--ignore-failed-read",
        "--directory", source
    ]
    for ex in excludes: tar_cmd.extend(["--exclude", ex])

    pv_cmd = ["pv", "-pbert", "-s", str(source_usage)]
    pzstd_cmd = ["pzstd", "-c"]

    # File name handling
    version_id = 0
    image_name_full = ""
    while True:
        try:
            image_name_full = f"{image_name_prepend}-{metadata['image_name']}-{version_id}"
            response = httpx.get(f"{CLONIX_API_URL}/api/v1/images/{image_name_full}")
            if response.status_code == 200:
                version_id += 1
                continue
            break

        except Exception as e:
            log_error(e, "Unknown error while searching the image database")
            return False

    # Write the new file name to the metadata object
    metadata['image_name'] = image_name_full

    if to_file:
        destination = os.path.abspath(os.path.join(CLONIX_LOCAL_IMAGE_DIR, f"{image_name_full}.tar.zst"))
    else:
        destination = f"{CLONIX_API_URL}/api/v1/file/image"

    # Now we can do it.
    commands.do_freeze(image_name_full, source_usage, destination, source, to_file)
