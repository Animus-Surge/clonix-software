"""
Partitions given device given the following information

Runs parted as subprocesses
"""

import os
import subprocess

import parted

def create_disk_label(labeltype, disk):
    pass

def create_disk_partition(disk, parttype, fstype, start, end):
    pass

def format_disk_partition(part, fstype):
    pass

def confirm_all(confirm):
    pass
