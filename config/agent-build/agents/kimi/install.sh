#!/usr/bin/env bash
set -euo pipefail

npm install -g @moonshot-ai/kimi-code

# Remove native-build cache left under root's home by npm.
rm -rf /root/.cache/node-gyp

install -d /usr/share/licenses/kimi

curl \
  -fsSL \
  --retry 8 \
  --retry-all-errors \
  --retry-delay 2 \
  --max-time 300 \
  https://raw.githubusercontent.com/MoonshotAI/kimi-code/refs/heads/main/LICENSE \
  -o /usr/share/licenses/kimi/LICENSE
