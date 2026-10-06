#!/bin/sh

# IDE: Visual Studio Code
# Plugin: Claude Code
# Plugin ID: anthropic.claude-code

# VS Code calls its process wrapper as:
# <wrapper> <bundled-claude-binary> <Claude arguments...>
shift

exec aicage claude "$@"
