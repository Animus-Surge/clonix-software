"""
Clonix: util/pretty.py

Pretty-printers, human readable formatters
"""

from typing import Tuple


def raw_to_readable(value: int) -> str:
    """
    Converts a raw number of bytes into a human readable format.

    E.g. 1024 = 1.00 KiB; 5432100 = 5.18 MiB

    Parameters:
        value (int): The raw number of bytes to convert

    Returns:
        str - The human readable form
    """

    if value <= 0: return '0B' # Just give zero bytes for negative and zero values
    size = float(value)
    
    index = 0
    units = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EB']

    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1

    if index == 0: return f'{int(size)}B'
    return f'{size:.2f}{units[index]}'

def disk_to_list_view(disk: Tuple[str, str, int]):
    pass
