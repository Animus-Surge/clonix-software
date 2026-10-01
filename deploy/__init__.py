"""
Clonix: deploy/__init__.py

Deployment processes
"""

import os
import shutil
import subprocess

from loguru import logger

from deploy.first_run import generate_init
from deploy.subvolumes import mk_subvol

from util import gvars

def deploy(source_filepath: str, drive_structure: dict):
    pass

