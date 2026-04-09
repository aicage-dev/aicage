#!/usr/bin/env bash
set -euo pipefail

curl_args=(
  -fsSL
  --retry 8
  --retry-all-errors
  --retry-delay 2
  --max-time 300
  -H "Accept: application/vnd.github+json"
)

if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  curl_args+=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
fi

curl \
  "${curl_args[@]}" \
  https://api.github.com/repos/block/goose/releases/latest \
  | jq -r '.name | ltrimstr("v")'
