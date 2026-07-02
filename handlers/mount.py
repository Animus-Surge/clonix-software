"""
Clonix: handlers/mount.py

Mounting and unmounting
"""

import os

from loguru import logger

import util

def mount_device(device: str, mountpoint: str, mkdir=False, opts='') -> bool:
    """
    Mounts a device or path to a specified mountpoint.

    Parameters:
        device (str): The device or path to mount
        mountpoint (str): The location to mount the device to
        mkdir (bool): Whether the mountpoint should be created
        opts (str): Mount options to pass into `mount`

    Returns:
        bool: Whether or not the mount is successful or not.
    """
    if '=' not in device or not os.path.exists(device) or not 'bind' in opts:
        logger.error(f"Device {device} not found.")
        return False

    if not os.path.exists(mountpoint):
        if mkdir:
            os.mkdir(mountpoint)
        else: return False

    if '=' in device:
        devtype, value = device.split('=')

        match devtype:
            case 'LABEL':
                if value not in os.listdir('/dev/disk/by-label/'):
                    return False
            case 'UUID':
                if value not in os.listdir('/dev/disk/by-uuid/'):
                    return False

            case _:
                return False

    return util.run_subprocess(f'mount {f"-o {opts}" if len(opts) > 0 else ''} {device} {mountpoint}')

def mount_binds(target):
    """
    Mounts bind directories (dev, proc, run sys).

    Parameters:
        target (str): The target prefix where the mounts should take place

    Returns:
        bool: True if all mounts successful, false otherwise.
    """
    for bind_dir in ['dev', 'proc', 'run', 'sys']:
        if not mount_device(bind_dir, f'{os.path.join(target, bind_dir)}', opts='--bind'): return False
    return True

def unmount_path(path: str, recursive=False) -> bool:
    """
    Perform an umount, given the mountpoint.

    Parameters:
        path (str): The mountpoint
        recursive (bool): Unmount recursive mounts

    Returns:
        bool: Whether the unmount is successful or not.
    """

    if not os.path.ismount(path): 
        logger.error(f"{path} is not mounted.")
        return False

    return util.run_subprocess(f'umount {"--recursive" if recursive else ""} {path}')

def unmount_device(device: str, recursive=False) -> bool:
    """
    Perform an umount, given the device.

    Parameters:
        device (str): The device
        recursive (bool): Unmount recursive mounts

    Returns:
        bool: Whether the unmount is successful or not.
    """

    # TODO: implement
    return False
