#!/bin/bash

## CloNIX script - target_configure_encryption
# Configures TPM encryption, based on given arguments.
# Should be run in chroot environment
#
# Usage: ./target_configure_tpm.sh <target> <pw> <tpm2> [pcrs]
# Arguments: -p <pw>   Use this password instead of prompt
# Assumes we are running in chroot

pw=$1
target=$2
tpm2=$3

if [[ ! -z $4 ]]; then
  pcr_opt="--tpm2-pcrs=$4"
  pcr_opt_12="-r $4" # TODO: fix to write multiple options as an array, comma separated
else
  pcr_opt=
fi

if [[ $tpm2 == yes ]]; then
  PASSWORD="$pw" systemd-cryptenroll $target --tpm2-device=auto $pcr_opt
else
  tpm_takeownership -y -z
  dd if=/dev/urandom of=/run/user/1000/tpm.key bs=1 count=256
  tpm_nvdefine -i 1 -s 256 -y -z -p 'READ_STCLEAR|OWNERWRITE'
  tpm_nvwrite -i 1 -s 256 -z -f /run/user/1000/tpm.key
  shred -u /run/user/1000/tpm.key
fi
