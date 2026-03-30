#!/bin/bash

## CloNIX script - format_boot_encrypted.sh
# Formats an encrypted boot drive
# Usage: ./format_boot_encrypted.sh [-b] <drive> <password>
# Arguments: <drive>   The drive to format (REQUIRED)
#            -b        Format the root partition as btrfs instead of ext4
#
# Note: This does NOT enable the tpm. That's handled by `enable_tpm.sh`
# Note: Options must come before the positional argument.

usage() {
  echo "Usage: $0 [-b] <drive>"
  echo ""
}

use_btrfs=false
prefix=

eval set -- "$opts"

echo "I: format_boot_encrypted.sh"

while getopts "b" opt; do
  case $opt in
    b) use_btrfs=true ;;
    *) usage() >&2 ; exit 1 ;;
  esac
done

shift $((OPTIND -1))

echo "I: Selecting drive $1"
echo "I: Creating new GPT label"
parted $1 -- mklabel gpt > /dev/null

if echo $1 | grep nvme; then
  prefix=p
fi

echo "I: Partitioning ${1}${prefix}1"
parted $1 -- mkpart primary fat32 8M 1G > /dev/null

echo "I: Partitioning ${1}${prefix}2"
parted $1 -- mkpart primary ext4 1G 3G > /dev/null

echo "I: Partitioning ${1}${prefix}3"
if $use_btrfs; then
  parted $1 -- mkpart primary btrfs 1G 100%
else
  parted $1 -- mkpart primary ext4 1G 100%
fi

echo "I: Formatting ${1}${prefix}1 as vfat..."
yes | mkfs.vfat -F 32 -n boot ${1}${prefix}1

echo "I: Formatting ${1}${prefix}2 as ext4..."
yes | mkfs.ext4 ${1}${prefix}2

echo "I: Formatting encrypted ${1}${prefix}3..."
echo -n $2 | cryptsetup luksFormat -q "${1}${prefix}3" -
echo -n $2 | cryptsetup luksOpen "${1}${prefix}3" dm_crypt-0 -

if $use_btrfs; then
  echo "I: Formatting encrypted volume as btrfs..."
  yes mkfs.btrfs "/dev/mapper/dm_crypt-0"
else
  echo "I: Formatting encrypted volume as ext4..."
  yes | mkfs.ext4 "/dev/mapper/dm_crypt-0"
fi

# Now mount to /target
echo "I: Mounting /target..."

mkdir /target | true
mount /dev/mapper/dm_crypt-0 /target
mkdir /target/boot
mount ${1}${prefix}2 /target/boot
mkdir /target/boot/efi
mount ${1}${prefix}1 /target/boot/efi

# Bind mounts
for dir in dev proc run sys; do
  mount --bind=$dir /target/$dir
done

echo "I: Done."









