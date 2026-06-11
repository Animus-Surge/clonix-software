"""
Clonix: deploy/__init__.py

Deployment processes
"""

import os

from loguru import logger

def start_deployment(source, target, opts: dict = {}):
    if not os.path.exists(source) or not os.path.exists(target):
        logger.fatal("Given source or target does not exist.")
        return False

    """
    opts:

    {
      'btrfs': {
        'use': <bool>,
        'default_volumes': <bool>
        'subvols': [
          {
            'name': <string>,
            'path': <string>,
            'device': <string>
          }
        ]
      },
      'luks': <bool>,
      'tpm': <bool>,
      'swap': <bool>
    }
    """

    logger.info("Starting deployment on {}".format(target))


    # Partition (DOES NOT HANDLE SUBVOLUMES)
    # Copy
    # Btrfs?
    # Setup
    # - Kernel
    # - 
    # init.sh
    # Done


    pass


