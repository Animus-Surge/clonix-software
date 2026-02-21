#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "FATAL: Must be run as root!"
  exit 1
fi

if [[ -z $1 ]]; then
  echo "ERROR: needs drive to mount"
  exit 1
fi

cryptsetup luksOpen $1 dm_crypt-0
if [ $? -eq 0 ]; then
  sleep 5s
  mount /dev/dm-1 /source
  exit 0
else
fi

mount $1 /source
