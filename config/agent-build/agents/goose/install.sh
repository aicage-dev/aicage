#!/usr/bin/env bash
set -euo pipefail

GOOSE_BIN_DIR=/usr/local/lib/goose
install -d "${GOOSE_BIN_DIR}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

curl \
  -fsSL \
  --retry 8 \
  --retry-all-errors \
  --retry-delay 2 \
  --max-time 300 \
  https://github.com/aaif-goose/goose/releases/download/stable/download_cli.sh |
  GOOSE_BIN_DIR="${GOOSE_BIN_DIR}" \
    CONFIGURE=false \
    bash

install -m 0755 "${script_dir}/goose" /usr/local/bin/goose
