#!/bin/sh

# IDE: Visual Studio Code
# Plugin: Claude Code
# Plugin ID: anthropic.claude-code

# VS Code calls its process wrapper as:
# <wrapper> <bundled-claude-binary> <Claude arguments...>
shift

# run agent in aicage container while passing arguments
exec aicage claude "$@"
