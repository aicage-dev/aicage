# How to debug

First step: print the generated Docker command.

```bash
aicage --dry-run <agent>
```

This helps confirm mounts, env vars, and Docker args before running.

If you need to inspect the container directly, use one of these shell options:

## 1) Override the entrypoint

This starts a shell as root before the entrypoint runs.

```bash
aicage --entrypoint bash -- <agent>
```

You are in the image as root, with the entrypoint skipped.

## 2) Override the agent start command

This still runs the entrypoint, sets up the user, and drops you into a shell instead of starting
an agent.

```bash
aicage -e AICAGE_ENTRYPOINT_CMD=bash -- <agent>
```
