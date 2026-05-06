# CloNIX system/partition_manager.py
# Partition management system
# Creates and reads out the partition tables of all drives

import json
import os
import subprocess

FLAG_ESP = 0x1

# Takes a dictionary representing the partition layout of the target and executes it
def execute_partition_layout(partlayout):
    pass

# Read and output the partition table as json
def read_partition_table(drive): 
    table = {}

    try:
        output = json.loads(subprocess.check_output(['lsblk', '-JOb'], check=True))

        for dev in output.get("blockdevices"):
            if dev.get("name") == partlayout.split('/')[-1]:
                partitions = {}
                total_partition_size = 0

                for part in dev.get("children"):

                    part_dict = {
                            "fstype": part.get("fstype"),
                            "uuid": part.get("uuid"),
                            "size": part.get("size")
                    }

                    partitions[part.get("name")] = part_dict

                    total_partition_size += part.get("size")

                
                table[dev.get("name")] = {
                        "id": dev.get("id-link"),
                        "size": util.bytes_to_human_readable(dev.get("size")),
                        "used": util.bytes_to_human_readable(total_partition_size),
                        "serialnum": dev.get("serial"),
                        "partitions": partitions
                        }
                return table
    except:
        pass

    return {}
    

def create_gpt_table(drive):
    pass

def create_partition(drive, partnum, fs, start, size, flags=0x0):
    pass


# BEGIN: TESTING FUNCTIONS

def test_read_partition_table():
    pass

def test_create_gpt_table():
    pass

def test_create_partition():
    pass

# END: TESTING FUNCTIONS

