#!/bin/bas

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

eval set -- "$opts"

while getopts "b" opt; do
  case $opt in
    b) use_btrfs=true ;;
    *) usage() >&2 ; exit 1 ;;
  esac
done

shift $((OPTIND -1))


echo $use_btrfs
echo $1
echo $2

exit # Quit before I do any damage

echo "INFO: Selecting drive $1"
echo "INFO: Creating new GPT label"
parted $1 -- mklabel gpt > /dev/null


echo "INFO: Partitioning ${1}1"
parted $1 -- mkpart primary fat32 8M 1G > /dev/null

echo "INFO: Partitioning ${1}2"
parted $1 -- mkpart primary ext4 1G 3G > /dev/null

echo "INFO: Partitioning ${1}3"
if $use_btrfs; then
  parted $1 -- mkpart primary btrfs 1G 100%
else
  parted $1 -- mkpart primary ext4 1G 100%
fi

echo "INFO: Formatting ${1}1 as vfat..."
yes | mkfs.vfat -F 32 -n boot ${1}1

echo "INFO: Formatting ${1}2 as ext4..."
yes | mkfs.ext4 ${1}2

echo "INFO: Formatting encrypted ${1}3..."
echo -n $2 | cryptsetup luksFormat -q "${1}3" -
echo -n $2 | cryptsetup luksOpen "${1}3" dm_crypt-0 -

if $use_btrfs; then
  echo "INFO: Formatting encrypted volume as btrfs..."
  yes mkfs.btrfs "/dev/mapper/dm_crypt-0"
else
  echo "INFO: Formatting encrypted volume as ext4..."
  yes | mkfs.ext4 "/dev/mapper/dm_crypt-0"
fi

echo "SUCCESS: Done."









