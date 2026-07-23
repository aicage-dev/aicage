# How it works

`aicage` runs the agent inside a Docker container and mounts the parts of your host that the agent
needs. This keeps the host boundary tight while preserving a normal developer workflow.

## What gets mounted

Typical mounts:

- Your project directory.
- Agent config files or directories (for example `~/.claude`, `~/.config/github-copilot`, etc.).
- Optional mounts:
  - Git support mounts (git config, GnuPG and SSH keys for signing commits).
  - Extension-defined shares (host mounts).
  - Docker socket (only when you pass `--docker`).

The agent starts in your project directory. On Windows, the path is the WSL-style path (for
example `/mnt/c/...`).

## What the container provides

- A Linux base image with a full dev toolchain.
- The chosen agent installed on top of that base.
- A startup entrypoint that:
  - on normal Linux runs, creates a user matching your host UID/GID and switches into it
  - on root-compatible setups such as Windows compatibility or rootless Docker, stays on
    container root and uses `/root`

## Config flow

- On first run, `aicage <agent>` opens the default setup screen.
- The UI lets you review and change the saved config for that agent in the current project before
  starting.
- Your per-project config lives at `~/.aicage/projects/<sha256>.yaml`.
- `aicage --config` shows the active project config and its location.
- `aicage --menu simple` keeps the classic line-based prompt flow available.
- `aicage --menu none` skips menus and uses defaults.

Use `aicage --config remove` only when you want to reset saved config entirely. To reset only one
agent entry, use `aicage --config remove <agent>`.
