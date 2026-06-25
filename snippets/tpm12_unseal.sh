#!/bin/bash

mkdir -p /mnt/tpm
mount -t tmpfs tmpfs /mnt/tpm

if ! tpm_nvread -i 1 >/dev/null 2>&1; then
  tcsd -f &
fi

for attempt in {1..6}; do
  if tpm_nvread -i 1 -f /mnt/tpm/key; then
    break
  fi
done

if [[ -e /mnt/tpm/key ]]; then
  echo "TPM1.2: Unseal successful."
else
  echo "TPM1.2: Unseal unsuccessful."
fi
