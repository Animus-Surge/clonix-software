"""
CloNIX: freeze/gen_metadata.py

Creates image metadata
"""

import util
import datetime

def generate(source: str, image_size_decompressed: int) -> dict:
    os_info = util.read_os_version(source)

    return {
        "image_name": f"{os_info['ID']}-{os_info['VERSION_ID']}-{datetime.datetime.now().strftime('%Y-%m-%d')}",
        "image_os": os_info["NAME"],
        "image_code": os_info["VERSION_CODENAME"],
        "image_size_bytes": image_size_decompressed,
    }
