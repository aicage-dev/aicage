#!/usr/bin/env bash
set -euo pipefail

npm install -g @augmentcode/auggie

install -d /usr/share/licenses/auggie
curl \
  -fsSL \
  --retry 8 \
  --retry-all-errors \
  --retry-delay 2 \
  --max-time 300 \
  https://raw.githubusercontent.com/augmentcode/auggie/refs/heads/main/LICENSE.md \
  -o /usr/share/licenses/auggie/LICENSE.md
