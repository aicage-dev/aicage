#!/bin/sh

# IDE: Visual Studio Code
# Plugin: ChatGPT
# Plugin ID: openai.chatgpt

# run agent in aicage container while passing arguments
exec aicage --allow-home-mount codex "$@"
