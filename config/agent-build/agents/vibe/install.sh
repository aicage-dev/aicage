#!/usr/bin/env bash
set -euo pipefail

curl \
  -fsSL \
  --retry 8 \
  --retry-all-errors \
  --retry-delay 2 \
  --max-time 300 \
  https://mistral.ai/vibe/install.sh |
  UV_TOOL_DIR=/opt/uv/tools \
    UV_TOOL_BIN_DIR=/usr/local/bin \
    bash

install -d /usr/share/licenses/vibe
curl \
  -fsSL \
  --retry 8 \
  --retry-all-errors \
  --retry-delay 2 \
  --max-time 300 \
  https://raw.githubusercontent.com/mistralai/mistral-vibe/refs/heads/main/LICENSE \
  -o /usr/share/licenses/vibe/LICENSE

# Remove root-home artifacts left by the installer.
uv cache clean
