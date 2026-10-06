#!/bin/sh

# IDE: JetBrains IDEs
# Plugin: CC GUI (Claude or Codex)
# Plugin ID: com.github.idea-claude-code-gui

# run agent in aicage container while passing arguments
exec aicage claude "$@"
