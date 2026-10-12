#!/usr/bin/env bash
set -euo pipefail

if command -v pip >/dev/null 2>&1; then
  _pip_cmd="pip"
elif command -v pip3 >/dev/null 2>&1; then
  _pip_cmd="pip3"
else
  exit 1
fi

"${_pip_cmd}" index versions mistral-vibe 2>/dev/null | sed -n '1{s/.*(\(.*\)).*/\1/p;}'
