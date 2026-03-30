## CloNIX scripts/gen_fstab_encrypted.py
# Generate encrypted variant

def gen_fstab_encrypted(device:str, is_btrfs=False, subvols=[]):
    """Generate target's fstab, with encrypted options. Supports btrfs subvolumes.
    
    Note: this assumes the standard 3 partition layout: boot_efi, boot, and encrypted root.
    TODO: support nonstandard partition layouts

    Args:
        device (str): The physical device to use (e.g. /dev/sda)
        is_btrfs (bool): Whether to specify this drive's **root** partition to be btrfs
        subvols (list): btrfs subvolumes to put on fstab

    Returns:
        0 if succeeded.
        1 if errored. Error message is always printed.
    """
    
    # Gather uuids
    part_uuids = get_part_uuids(device)

    if len(part_uuids) == 0:
        print("E: Failed to get partition information.")
        return 1
    
    print("I: Gathered partition UUIDS:")
    ind=1
    for uuid in part_uuids:
        print("D: {ind} {uuid}")
        ind += 1

    print("I: Writing /target/etc/fstab...")

    # Create fstab entries
    fstab_text = [
        "# /etc/fstab: static filesystem information.",
        "#",
        "# Use 'blkid' to print the univerally unique identifier for a",
        "# device; this may be used with UUID= as a more robust way to name devices",
        "# that works even if disks are added and removed. See fstab(5).",
        "#",
        "# <file system> <mount point>    <type>  <option>       <dump>  <pass>"
    ]

    # Entry 1: efi partition
    fstab_text.append(f"/dev/disk/by-uuid/{part_uuids[0]} /boot/efi vfat defaults 0 0")
    # Entry 2: boot partition
    fstab_text.append(f"/dev/disk/by-uuid/{part_uuids[1]} /boot ext4 defaults,nodev,nosuid 0 1")
    # Entry 3: root partition -- TODO: subvolumes
    fstab_text.append(f"/dev/disk/by-id/dm-uuid-CRYPT-LUKS2-{part_uuids[3].replace('-', '')} {root_fs} defaults 0 1")

    # Last entry: swapfile
    fstab_text.append(f"/swap.img none swap sw 0 0")

    # Now we write it to /target/etc/fstab
    with open("/target/etc/fstab", "w") as f:
        for line in fstab_text:
            f.write(line)
            f.write("\n")

    print("I: Done.")

    return 0

def gen_fstab(device, is_btrfs=False, subvols=[]):
    """Generate target's fstab, with encrypted options. Supports btrfs subvolumes.
    
    Note: this assumes the standard 2 partition layout: boot_efi and root.
    TODO: support nonstandard partition layouts

    Args:
        device (str): The physical device to use (e.g. /dev/sda)
        is_btrfs (bool): Whether to specify this drive's **root** partition to be btrfs
        subvols (list): btrfs subvolumes to put on fstab
    """
    pass

def get_part_uuids(drive):
    try:
        result = subprocess.run(
                ['lsblk', '-no', 'UUID', drive],
                capture_output=True,
                text=True,
                check=True
                )

        uuids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return uuids
    except subprocess.CalledProcessError as e:
        print(f"E: Could not read drive '{drive}'. {e.stderr}")
        return []

