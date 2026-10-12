#!/bin/sh

# IDE: Visual Studio Code
# Plugin: Claude Code
# Plugin ID: anthropic.claude-code

agent=claude

# VS Code calls its process wrapper as:
# <wrapper> <bundled-claude-binary> <Claude arguments...>
claude_binary=$1
shift

# setup log dir and file
log_dir="$HOME/.aicage/logs/ide-plugins/$agent"
mkdir -p "$log_dir"
log_file="$log_dir/$agent-$(date +%Y%m%d-%H%M%S).log"

# log request
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

# run agent in aicage container while passing arguments and logging stderr output
exec aicage "$agent" "$@" 2>>"$log_file"
