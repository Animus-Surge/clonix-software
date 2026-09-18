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

def start_freeze(source: str, image_name_prepend: str = "", to_file = False):
    # Gather information for metadata
    source_usage = shutil.disk_usage(source).used
    metadata = gen_metadata.generate(source, source_usage)

    # Check for required and optional binaries
    if not os.path.exists("/usr/bin/tar") or not os.path.exists("/usr/bin/pzstd"):
        return False

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

    metadata['image_name'] = image_name_full

    # Lets start
    try:
        # Save the metadata
        r = httpx.post(f"{CLONIX_API_URL}/api/v1/images", data=metadata)
        if r.status_code != 201:
            logger.error("Failed to write image metadata to server.")
            return False

        if to_file:
            file = open(metadata['image_name'], 'wb')

        # Start subprocesses
        proc1 = subprocess.Popen(tar_cmd, stdout=subprocess.PIPE)
        proc2 = subprocess.Popen(pv_cmd, stdin=proc1.stdout, stdout=subprocess.PIPE)
        if to_file:
            proc3 = subprocess.Popen(pzstd_cmd, stdin=proc2.stdout, stdout=file)
        else:
            proc3 = subprocess.Popen(pzstd_cmd, stdin=proc2.stdout, stdout=subprocess.PIPE)

        # Allow upstream SIGPIPE
        if proc1.stdout:
            proc1.stdout.close()
        if proc2.stdout:
            proc2.stdout.close()

        # Store the file to the server
        req_headers = {}
        req_headers.setdefault("Content-Type", "application/octet-stream")
        with httpx.Client(timeout=None) as client:
            response = client.post(f"{CLONIX_API_URL}/api/v1/file/image", content=proc3.stdout, headers=req_headers)

        # We're done
        proc3.wait()
        proc2.wait()
        proc1.wait()

        if proc1.returncode != 0 or proc2.returncode != 0 or proc3.returncode != 0:
            raise subprocess.CalledProcessError(proc1.returncode or proc2.returncode or proc3.returncode, "Pipeline error")

        response.raise_for_status()
        logger.success("Image freeze complete.")
        return True

    except Exception as e:
        log_error(e, "Unknown error while writing new image to database")
        return False
