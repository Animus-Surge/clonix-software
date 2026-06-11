#!/usr/bin/env bash

# Updater script; takes the arguments that were passed to main.py

echo "I: update: Updating clonix..."

if $(git rev-parse --is-inside-work-tree); then
  git pull origin prod --ff-only

  if [[ $? -ne 0 ]]; then
    echo "E: Failed to update."
    exit 1

else
  echo "N: update: Not a git repo; using curl to download latest."
  dl_url="https://github.com/Animus-Surge/clonix/archive/refs/heads/latest.tar.gz"

  if curl -sI "$dl_url" | grep -q "200 OK"; then
    curl -sL "$dl_url" | tar -xzf - --strip-components=1
    echo "S: update: Done."
  else
    echo "E: Failed to download from ${dl_url}."
    exit 1
  fi
fi

exec python3 ./main.py $@
