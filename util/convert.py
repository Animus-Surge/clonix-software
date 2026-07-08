"""
Clonix: util/pretty.py

Pretty-printers, human readable formatters
"""

import re

from util import constants


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
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB']

    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1

    if index == 0: return f'{int(size)}B'
    return f'{size:.2f}{units[index]}'

def readable_to_raw(value: str, size: int = 0) -> int:
    """
    Converts a readable value (e.g. 400G, 7TiB, 80MB) to a byte count.

    Parameters:
        value (str): The readable value
        size (int): (Default: 0) The size context for percentage values

    Returns:
        int: The final value, 0 if value (and size if %) is 0 or an error occurred.
    """

    value = value.strip().upper()

    # Percentage checking, needs size context
    if '%' in value:
        if size == 0: return 0

        percentage = float(value.rstrip('%'))
        return int((percentage / 100.0) * size)

    match = re.match(r'^(\d+(?:\.\d+)?)\s*([KMGTP]I?B?)?$', value)
    if not match:
        return 0

    number,unit = match.groups()
    number = float(number)

    if not unit: return int(number)

    unit = unit[0]
    return int(number * constants.BYTE_MULTIPLIERS.get(unit, 1))

