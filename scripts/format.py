"""
format.py

Format target drive, given drive and partition list
"""

"""
Partition list format:
[
    {
        "type": <fstype:str>,
        "size": <size_in_gb:float>
    },
    ...
]

Partitions listed in order
"""

import subprocess

def format(target: str, partitions: list):
    print(f"I: Formatting {target}...")


    try:
        subprocess.run(
            ["parted", target, "--", "mklabel", "gpt"],
            check=True)
    except subprocess.CalledProcessError as e:
        return 1

    for partition in partitions:
        try:
            subprocess.run(
                ["parted", target, "--", ""],
                check=True
            )
        except subprocess.CalledProcessError as e:
            return 1
    return 0
