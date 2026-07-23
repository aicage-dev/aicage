# CLI options

This page covers the non-default CLI paths and reference-style options.

For normal interactive use, run:

```bash
aicage <agent>
```

That opens the default setup screen.

## Core options

- `--dry-run`: print the composed `docker run` command without executing it.
- `--menu ui|simple|none`: use the default setup screen, the classic line-based prompt menu,
  or no menu.
- `--docker`: mount `/run/docker.sock` into the container to enable Docker-in-Docker workflows.
- `--share <path>`: mount a host path into the container. Repeatable; append `:ro` for read-only.
- Extensions can also define extra shares (host mounts).
- `--config`: print the project config path and its contents.
- `--config remove [<agent>]`: remove the whole project config file, or only one agent entry.

## Menu modes

- `aicage <agent>` and `aicage --menu ui <agent>` use the default setup screen.
- `aicage --menu simple <agent>` uses the older line-based prompt flow.
- `aicage --menu none <agent>` skips menus and accepts defaults.

In normal use, the default setup screen is the intended path.

## Config inspection and removal

Most users can review and change settings by rerunning `aicage <agent>` and using the setup screen.

`--config` and `--config remove` are mainly useful for inspection, recovery, or automation:

- `aicage --config`: print the project config path and contents
- `aicage --config remove`: remove the whole saved project config
- `aicage --config remove <agent>`: remove only one saved agent entry

## Proxy env forwarding

When set on the host, `aicage` forwards these proxy env vars to local image builds and runtime:
`HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, and `NO_PROXY`.

## Info

- `-h`, `--help`: show usage and exit.
- `--version`: print the `aicage` version and exit.

## Examples

Print the docker command without running it (replace `<agent>` with your agent):

```bash
aicage --dry-run <agent>
```

Use the default setup screen:

```bash
aicage <agent>
```

Use the classic line-based prompt menu:

```bash
aicage --menu simple <agent>
```

Run without menus and accept defaults:

```bash
aicage --menu none <agent>
```

Mount the Docker socket for Docker-in-Docker:

```bash
aicage --docker <agent>
```

Share a host directory into the container (read-only):

```bash
aicage --share /data:ro <agent>
```

Show the project config path and contents:

```bash
aicage --config
```

Remove only the `codex` entry from the project config:

```bash
aicage --config remove codex
```
