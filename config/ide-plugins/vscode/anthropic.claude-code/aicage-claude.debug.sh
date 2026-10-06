#!/bin/sh

agent=claude

# VS Code calls its process wrapper as:
# <wrapper> <bundled-claude-binary> <Claude arguments...>
claude_binary=$1
shift

script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
log_dir="$script_dir/log"
mkdir -p "$log_dir"
log_file="$log_dir/claude-$(date +%Y%m%d-%H%M%S).log"

{
  echo "=== aicage-$agent VS Code shim ==="
  echo "timestamp: $(date '+%Y-%m-%dT%H:%M:%S%z')"
  echo "pwd: $(pwd)"
  echo "agent: $agent"
  printf 'bundled Claude binary: %s\n' "$claude_binary"
  printf 'argv: %s\n' "$*"
  echo "argc: $#"
  echo "---"
} >>"$log_file"

exec aicage "$agent" "$@" 2>>"$log_file"
