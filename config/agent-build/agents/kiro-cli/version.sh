#!/usr/bin/env bash
set -euo pipefail

curl \
  -fsSL \
  --retry 8 \
  --retry-all-errors \
  --retry-delay 2 \
  --max-time 300 \
  https://prod.download.cli.kiro.dev/stable/latest/manifest.json |
  jq -r '.version'
