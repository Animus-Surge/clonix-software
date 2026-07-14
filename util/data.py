"""
Clonix: data.py

Data structures and handling
"""

from dataclasses import dataclass, field

from typing import List

@dataclass
class BtrfsSubvol:
    name: str
    mountpoint: str

    mountopts: str = ''

@dataclass
class Partition:
    index: int # Field dynamically updated
    fstype: str
    mountpoint: str

    # RAW values (i.e. number of bytes)
    # Used to determine partition ordering and size constraints
    start: int
    size: int
    end: int

    # Readable values (i.e. 500G, 2.6T)
    # Actually get passed to `parted`
    start_readable: str = ''
    end_readable: str = ''

    # Optional fields
    label: str = ''  # Filesystem label
    dev_name: str = '' # i.e. nvme0n1p4 or sda2, or md126p2. 
    flags: List[str] = field(default_factory=list) # Flag names
    
    # Encryption settings
    encrypted: bool = False
    encrypted_volume_name = ""
    passphrase = '' # Here for cases where multiple encrypted devices have different passphrases (which is more secure)

    subvols: List[BtrfsSubvol] = field(default_factory=list) # Btrfs subvolumes; blank for optional

