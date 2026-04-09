#!/usr/bin/env bash
set -euo pipefail

# Codex warns if /usr/bin/bwrap is missing on Windows-hosted runs.
if command -v apk >/dev/null 2>&1; then
  apk add --no-cache bubblewrap
elif command -v dpkg >/dev/null 2>&1; then
  apt-get update
  apt-get install -y --no-install-recommends bubblewrap
  apt-get clean
  rm -rf /var/lib/apt/lists/*
elif command -v rpm >/dev/null 2>&1; then
  dnf install -y bubblewrap
  dnf clean all
else
  echo "[install_codex] Unsupported distro: unable to install bubblewrap." >&2
  exit 1
fi

npm install -g @openai/codex

install -d /usr/share/licenses/codex
curl \
  -fsSL \
  --retry 8 \
  --retry-all-errors \
  --retry-delay 2 \
  --max-time 300 \
  https://raw.githubusercontent.com/openai/codex/main/LICENSE \
  -o /usr/share/licenses/codex/LICENSE
