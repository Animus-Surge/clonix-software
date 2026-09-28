"""
Clonix: deploy/setup.py

Initial setups and chroots
"""

import os
import shlex
import subprocess

from loguru import logger

import util
from util import constants
from util import gvars


