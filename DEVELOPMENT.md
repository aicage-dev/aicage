# Development Guide

This repo ships the `aicage` CLI. Image build logic lives in the other git-repos of owner `aicage`; this file is for
advanced/power users who want to tweak or extend things.

## Repo layout

- [README.md](README.md): end-user overview.
- [AGENTS.md](AGENTS.md): instructions for AI coding agents.
- `src/`: the `aicage` CLI implementation.
- `tests/`: Python tests for the CLI.
- `scripts/`: helper scripts.
- `doc/`: task notes for AI agents.

## Related projects (build docker images)

- [aicage-image-base/](https://github.com/aicage/aicage-image-base): builds base OS layers.
- [aicage-image/](https://github.com/aicage/aicage-image): builds agents on those bases.
- [aicage-image-util/](https://github.com/aicage/aicage-image-util): builds utility images for aicage runtime tasks.

## Local checks

Run `scripts/lint.sh` from an active virtualenv with `requirements-dev.txt` installed.

## Fork Setup

To test this repo from a fork:

1. Fork the repository.
2. Run `aicage` locally from source instead of trying to publish a forked package.
3. If you want to test against images from forks, update the fork-image block in `src/aicage/constants.py` so it
   points to the forked image repos and image sources.
4. Create and activate a virtualenv, then install `requirements-dev.txt`.
5. Run the CLI and tests locally from that source checkout.

Do not use the release flow of this repo as the fork test path. Releases here are for publishing the Python package,
which forks cannot do.

## Integration tests

Integration tests are opt-in because they require Docker and network access. Run them with:

```bash
AICAGE_RUN_INTEGRATION=1 pytest -m integration
```

Integration tests use a fake temp home on Linux and Windows so local runs do not write into the real user home.
macOS integration tests keep the real home because Docker Desktop on hosted macOS runners needs the real Docker user
config.

## Hosted runner coverage

GitHub-hosted macOS runners are only used for a small manual smoke subset. The full integration suite should stay on
Linux.

- macOS: use the dedicated hosted workflow for occasional smoke verification of remote builtin startup, local builtin
  rebuild flows, extension builds, and `--docker` behavior on a non-Linux host.
  The workflow installs Docker Desktop, starts it explicitly from `Docker.app`, and uploads `~/.aicage` logs on
  failure. Use the workflow-dispatch input to upload logs on success when debugging.
- Windows: verify manually on a local machine with the intended Docker Desktop + WSL2 setup.
- Full integration suite: keep it on Linux. Several tests assert Linux-only details such as `/proc/self/mountinfo`,
  `mountpoint`, and `stat -c`, so broad cross-platform execution would add noise without adding much signal.
