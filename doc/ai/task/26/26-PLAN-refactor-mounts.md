# Task 26 — Refactor handling of mounts from host (Plan)

## Goal

Unify all mount handling behind a single resolver pipeline with consistent rules, remove special-case mount handling,
ensure no mounts target container home directly, and use entrypoint symlinks for home-relative paths.

## Final rules (agreed)

- **No mounts target `/root` or `/home/<user>` directly.**
- Any host path under **host home** is mounted under a **fake home**:
  `/aicage/user-home/<relative-to-host-home>`.
- All other paths are mounted to the **container project path**:
  `container_project_path(host_path)`.
- Entry point symlinks mounts under `/aicage/user-home` into both:
  - `/root/<relative>`
  - `/home/<host-user>/<relative>`
- This guarantees home-relative paths are usable inside the container without interfering with user creation.

## Known implications

- **Project path under host home** is mounted under `/aicage/user-home/...` (never under `/home/<user>` or `/root`).
  The entry point creates symlinks to make it available in the container home after user creation.
- `--share` behavior changes for home-relative paths: they no longer mount directly under container home; they are
  symlinked from `/aicage/user-home/...`.

## Resolver abstraction (Python)

Use a **private Protocol + function implementations** to define a shared resolver interface.

### Private types

- `ResolvedArgs` dataclass (private):
  - `mounts: list[MountSpec]`
  - `env: list[EnvVar]`

- `Resolver` Protocol (private):
  - `def resolve(context: ConfigContext, agent: str, parsed: ParsedArgs | None) -> ResolvedArgs:`

### Resolver implementations (private package)

Create a private package such as `src/aicage/runtime/docker_args/resolvers/` with one module per use-case:

- `_project.py`
- `_agent_config.py`
- `_git_config.py`
- `_gpg.py`
- `_ssh.py`
- `_git_root.py`
- `_docker_socket.py`
- `_shares.py`

Each module exposes a single `resolve(...) -> ResolvedArgs` function.

### Planner

`src/aicage/runtime/docker_args/resolver.py` becomes the **single planner**:

- Iterate the resolver list in fixed order.
- Merge `ResolvedArgs.mounts` and `ResolvedArgs.env`.
- Apply the **home-mount rewrite rule**:
  - If host path is under `Path.home()`:
    - mount to `/aicage/user-home/<relative-to-host-home>`
  - Else:
    - mount to `container_project_path(host_path)`
- Deduplicate mounts and env as needed.

## Data model changes

- `DockerRunArgs`:
  - Remove `project_path` and `agent_config_mounts`.
  - Keep only `image_ref`, `merged_docker_args`, `agent_args`, `env`, `mounts`.

- `RunConfig` stays as-is (still used for build paths and selection).

## Entrypoint changes (aicage-image-base)

Update `../aicage-image-base/scripts/entrypoint.sh`:

- Remove special handling for `/aicage/host` and `/aicage/agent-config`.
- Add `setup_home_mount_links`:
  - Iterate mounts under `/aicage/user-home` and symlink into:
    - `/root/<relative>`
    - `/home/$AICAGE_HOST_USER/<relative>`
- Remove `/workspace` fallback handling and default `AICAGE_WORKSPACE=/workspace`.

## Env vars

- Add `AICAGE_HOST_USER` in `src/aicage/runtime/env_vars.py`.
- Set in `src/aicage/docker/_env.py`:
  - Windows: actual host username (not root)
  - Linux: same as `AICAGE_USER`

## Documentation updates (aicage.wiki)

Update:

- `How-It-Works.md`: explain mount routing and symlink fan-out via `/aicage/user-home`.
- `CLI-Options.md`: clarify that home-relative `--share` paths are available under container home via symlinks.

## Tests

Update tests to match new model:

- `tests/aicage/docker/test_run.py`
- `tests/aicage/runtime/test_run_plan.py`

Add tests for the new mount routing rule (home vs non-home paths).

Run:

- `pytest --cov=src --cov-report=term-missing`
- `scripts/lint.sh`

## Open approvals

- Note: The plan below is partially outdated. The second part of the change (updates in `../aicage-image-base` and
  `../aicage.wiki`) is already done.

## Pending deltas (as of commit `ad85ddb2`)

- `../aicage-image-base/scripts/entrypoint.sh` still needs updates for `/aicage/user-home` symlink fan-out and removal of
  `/aicage/host`, `/aicage/agent-config`, and `/workspace` fallback handling.
- `../aicage.wiki` updates are still pending (`How-It-Works.md`, `CLI-Options.md`).
- Resolver modules live in `src/aicage/runtime/docker_args/` (private modules) rather than a dedicated
  `resolvers/` subpackage.
- Mounts are deduplicated; env vars are appended without deduplication.
