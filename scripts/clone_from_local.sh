#!/bin/bash

## CloNIX scripts/clone_from_local.sh
# Clone filesystem image to target from local disk
#
# Note: this assumes any `format_*.sh` runs were successful
#
# clone_from_local.sh <file> <target>

usage() {
  echo "Usage: $0 <file>"
  echo "Where <file> - The source file"
  echo ""
  exit 1
}

if [[ $# -ne 2 ]]; then
  usage()
fi

set -euo pipefail

echo "INFO: Cloning $1 to /target..."

filesize=$(stat -c%s "$1")

if pzstd -dcq "$1" | pv -pberts $filesize | tar --xattrs --xattrs-include='*' -xpf - -C "/target"; then
  echo "SUCCESS: Copied $1 to /target."
else
  echo "ERROR: Failed to copy $1 to /target. See above for details."
  exit 1
fi
