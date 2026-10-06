#!/bin/sh

# VS Code calls its process wrapper as:
# <wrapper> <bundled-claude-binary> <Claude arguments...>
shift

exec aicage claude "$@"
