#!/bin/sh

name=${0##*/}
agent=${name#aicage-}
agent=${agent%.sh}
script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)

LOG_DIR="$script_dir/log"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$agent-$(date +%Y%m%d-%H%M%S).log"

{
  echo "=== aicage-$agent shim ==="
  echo "timestamp: $(date -Iseconds)"
  echo "pwd: $(pwd)"
  echo "agent: $agent"
  printf 'argv: %s\n' "$*"
  echo "argc: $#"
  echo "---"
} >>"$LOG_FILE"

exec /home/stefan/development/github/aicage/aicage/.venv/bin/aicage \
  --stdio \
  --menu none \
  --cap-add SYS_ADMIN \
  --security-opt seccomp=unconfined \
  --security-opt apparmor=unconfined \
  -- "$agent" "$@" 2>>"$LOG_FILE"
