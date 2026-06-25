#!/bin/sh

shred -u /mnt/tpm/key
umount /mnt/tpm
