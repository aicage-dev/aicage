#!/usr/bin/env bash
set -euo pipefail

# Goose seems to need libvulkan
if command -v apk >/dev/null 2>&1; then
  apk add --no-cache vulkan-loader
elif command -v dpkg >/dev/null 2>&1; then
  apt-get update
  apt-get install -y --no-install-recommends libvulkan1
  apt-get clean
  rm -rf /var/lib/apt/lists/*
elif command -v rpm >/dev/null 2>&1; then
  dnf install -y vulkan-loader
  dnf clean all
else
  echo "[install_goose] Unsupported distro: unable to install Vulkan loader." >&2
  exit 1
fi

curl \
  -fsSL \
  --retry 8 \
  --retry-all-errors \
  --retry-delay 2 \
  --max-time 300 \
  https://github.com/aaif-goose/goose/releases/download/stable/download_cli.sh | \
  GOOSE_BIN_DIR=/usr/local/bin \
  CONFIGURE=false \
  bash
