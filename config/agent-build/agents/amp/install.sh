#!/usr/bin/env bash
set -euo pipefail

curl \
  -fsSL \
  --retry 8 \
  --retry-all-errors \
  --retry-delay 2 \
  --max-time 300 \
  https://ampcode.com/install.sh |
  bash

if [[ -x "/root/.local/bin/amp" ]]; then
  install -m 0755 /root/.local/bin/amp /usr/local/bin/amp
elif [[ -x "/root/.amp/bin/amp" ]]; then
  install -m 0755 /root/.amp/bin/amp /usr/local/bin/amp
elif command -v amp >/dev/null 2>&1; then
  install -m 0755 "$(command -v amp)" /usr/local/bin/amp
fi

# Remove root-home artifacts left by the installer; the image uses /usr/local/bin.
rm -rf /root/.local/bin/amp /root/.amp/bin/amp

if ! command -v amp >/dev/null 2>&1; then
  echo "[install_amp] 'amp' executable not found after installation." >&2
  exit 1
fi
