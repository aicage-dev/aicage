#!/bin/sh

# IDE: JetBrains IDEs
# Plugin: CC GUI (Claude or Codex)
# Plugin ID: com.github.idea-claude-code-gui

agent=claude

# setup log dir and file
log_dir="$HOME/.aicage/log/ide-plugins/jetbrains/$agent"
mkdir -p "$log_dir"
log_file="$log_dir/$agent-$(date +%Y%m%d-%H%M%S).log"

# log request
{
  echo "=== aicage-$agent shim ==="
  echo "timestamp: $(date '+%Y-%m-%dT%H:%M:%S%z')"
  echo "pwd: $(pwd)"
  echo "agent: $agent"
  printf 'argv: %s\n' "$*"
  echo "argc: $#"
  echo "---"
} >>"$log_file"

# run agent in aicage container while passing arguments and logging stderr output
exec aicage "$agent" "$@" 2>>"$log_file"
