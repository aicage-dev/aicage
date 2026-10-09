#!/bin/sh
set -eu

# Debug wrapper for any aicage invocation.
# Usage: aicage.debug.sh <aicage arguments...>

log_dir="$HOME/.aicage/logs/ide-plugins/aicage"
mkdir -p "$log_dir"

run_id="$(date +%Y%m%d-%H%M%S)-$$"
log_file="$log_dir/aicage-$run_id.log"

{
  echo "=== aicage debug shim ==="
  echo "timestamp: $(date '+%Y-%m-%dT%H:%M:%S%z')"
  echo "pwd: $(pwd)"
  printf 'argv: %s\n' "$*"
  echo "argc: $#"
  echo "---"
} >>"$log_file"

# Preserve stdin/stdout and terminal behavior by replacing this process.
exec aicage "$@" 2>>"$log_file"
