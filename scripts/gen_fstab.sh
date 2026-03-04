#!/bin/bash

## CloNIX scripts/gen_fstab.sh
# Generate /target/etc/fstab
#
# Usage: gen_fstab.sh -b <target>

# Options
root_fstype=ext4
prefix=
btrfsopts=
if [[ $# -eq 2 ]]; then
  if echo $2 | grep nvme; then
    prefix=p
  fi

  if [[ $1 = "-b" ]]; then
    echo "NOTE: Using btrfs options"
    root_fstype=btrfs
    btrfsopts=",compress=zstd"
  fi
else
  if echo $1 | grep nvme; then
    prefix=p
  fi
fi

echo "INFO: Generating fstab..."

efi_uuid=$(blkid -s UUID -o value ${1}${prefix}1)
root_id=$(ls /dev/disk/by-id/dm-uuid-CRYPT-LUKS2*)
boot_uuid=$(blkid -s UUID -o value ${1}${prefix}2)

echo "NOTE: Retrieved EFI partition UUID $efi_uuid"
echo "NOTE: Retrieved boot partition UUID $boot_uuid"
echo "NOTE: Retrieved root partition LUKS ID $root_id"

echo "/dev/disk/by-uuid/$efi_uuid /boot/efi vfat defaults 0 0" > /target/etc/fstab
echo "/dev/disk/by-uuid/$boot_uuid /boot ext4 defaults,nodev,nosuid 0 1" >> /target/etc/fstab
echo "/dev/disk/by-id/$root_id / $root_fstype defaults${btrfsopts} 0 1" >> /target/etc/fstab

# TODO: subvolumes?

echo "NOTE: /target/etc/fstab generated:"
cat /target/etc/fstab

echo "SUCCESS: Generated fstab."
