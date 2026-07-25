# Entrypoint contract

`aicage` images start through `entrypoint.sh`.

Most users do not need to set its variables directly. `aicage` normally passes
them for you. This page is mainly useful when you:

- inspect `aicage --dry-run`
- debug a container startup issue
- run an image manually with `docker run`
- work on `aicage` or the image repos

## What the entrypoint expects

The entrypoint reacts to these environment variables:

| Variable                | Meaning                                                                                                                                                |
|-------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| `AICAGE_UID`            | Runtime user id inside the container.                                                                                                                  |
| `AICAGE_GID`            | Runtime group id inside the container.                                                                                                                 |
| `AICAGE_HOST_USER`      | Runtime user name inside the container.                                                                                                                |
| `AICAGE_HOME`           | Runtime home directory inside the container.                                                                                                           |
| `AICAGE_MOUNT_HOME`     | Host-home mount anchor when mounted home content lives somewhere other than the active `HOME`. Mainly relevant for Windows and root-compatible setups. |
| `AICAGE_WORKSPACE`      | Working directory the container starts in.                                                                                                             |
| `AICAGE_ENTRYPOINT_CMD` | Final command the entrypoint executes.                                                                                                                 |
| `TZ`                    | Optional timezone to apply inside the container.                                                                                                       |

## Normal behavior

For the common Linux case, `aicage` passes a host-like runtime identity:

- `AICAGE_UID` and `AICAGE_GID` match the host user
- `AICAGE_HOST_USER` matches the host user name
- `AICAGE_HOME` matches the mounted home path in the container

The entrypoint then:

- prepares that user if needed
- sets `HOME` and `USER`
- adjusts a few ownership details for workspace and mounted home paths
- starts the agent command

## Root behavior

If `AICAGE_UID=0` and `AICAGE_GID=0`, the entrypoint stays on container root
instead of switching to a generated user.

This is the behavior used for root-compatible setups such as:

- Windows / non-Linux host compatibility
- rootless Docker on Linux

In that case:

- `AICAGE_HOST_USER` is `root`
- `AICAGE_HOME` is `/root`
- `AICAGE_MOUNT_HOME` may point at a different mounted host-home path when
  mounted host-home content should still be visible under `/root`

What does not happen in that mode:

- no dynamic runtime user creation
- no host username matching
- no host-home remapping to become root's active `HOME`

## What users usually need to know

- `aicage --entrypoint bash -- <agent>` skips the entrypoint completely.
- `aicage -e AICAGE_ENTRYPOINT_CMD=bash -- <agent>` still runs the entrypoint,
  but starts a shell instead of the agent.
- If config files under your mounted home are not readable in the container,
  check the generated UID/GID, `HOME`, and mount paths first.

## Manual `docker run` example

Typical Linux non-root example:

```bash
docker run --rm -it \
  -e AICAGE_UID="$(id -u)" \
  -e AICAGE_GID="$(id -g)" \
  -e AICAGE_HOST_USER="$USER" \
  -e AICAGE_HOME="$HOME" \
  -e AICAGE_WORKSPACE="$PWD" \
  --mount "type=bind,src=$PWD,dst=$PWD" \
  ghcr.io/aicage/aicage:codex-ubuntu
```

Typical root-compatible example:

```bash
docker run --rm -it \
  -e AICAGE_UID=0 \
  -e AICAGE_GID=0 \
  -e AICAGE_HOST_USER=root \
  -e AICAGE_HOME=/root \
  -e AICAGE_MOUNT_HOME=/some/other/home \
  -e AICAGE_WORKSPACE="$PWD" \
  --mount "type=bind,src=$PWD,dst=$PWD" \
  ghcr.io/aicage/aicage:codex-ubuntu
```

That is only a debugging example. For normal use, prefer running through
`aicage` so the full mount and environment setup stays consistent.
