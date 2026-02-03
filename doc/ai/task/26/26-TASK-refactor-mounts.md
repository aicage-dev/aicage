# Task 26 — Refactor handling of mounts from host

## Affected code

- Project `aicage-image-base`: In `../aicage-image-base`
  - `scripts/entrypoint.sh` is the entrypoint script used in containers
  - Possible integration tests in `tests/smoke/default/*entrypoint*.bats` if we change `entrypoint.sh`
- Project `aicage`: In current repo, the handling of mounts to container, especially the dataclasses:
- `RunConfig` in `src/aicage/config/runtime_config.py`  

    ```python
    @dataclass(frozen=True)
    class RunConfig:
        project_path: Path
        agent: str
        context: ConfigContext
        selection: ImageSelection
        project_docker_args: str
        mounts: list[MountSpec]
        env: list[EnvVar]
    ```

- `DockerRunArgs` in `src/aicage/runtime/run_args.py`  

    ```python
    @dataclass
    class DockerRunArgs:
        image_ref: str
        project_path: Path
        agent_config_mounts: list[MountSpec]
        merged_docker_args: str
        agent_args: list[str]
        env: list[EnvVar] = field(default_factory=list)
        mounts: list[MountSpec] = field(default_factory=list)
    ```

  - Possibly existing documentation (`*.md` files)
- Project `aicage.wiki`: The user facing documentation in `../aicage.wiki`

## User in container

- Linux host: Same user as on host with same uid:gid
- Windows host: User root in container

## Current situation before this task

The current code handles mounts in several ways:

- `project_path`: Current path on host
  - python:
    - passes it as `AICAGE_WORKSPACE` env-var
    - mounts it to result of `container_project_path()` (see `src/aicage/paths.py`) in container
    - mounts it to `/workspace` in container (possibly historic or fallback, possibly unused)
    - separate from other mounts and possibly env-vars in both `RunConfig` and `DockerRunArgs`
  - entrypoint.sh:
    - handles it in its `setup_workspace()`, including the _fallback_ `/workspace`
    - changes directory to value of `AICAGE_WORKSPACE
- git-related paths: `~/.gitconfig`, `~/.gnupg` and `~/.ssh` on host and in container
  - python:
    - Not separate from other mounts and env-vars in both `RunConfig` and `DockerRunArgs`
    - Mounts them to specific subfolders of `/aicage/host` in containers
  - entrypoint.sh:
    - Creates symlinks to the users home for each specific subfolder of `/aicage/host` in containers
- `agent_config` paths: The files and folders shared from host for the agents config, often below users-home
  - python:
    - Reads them from `agent.yml` files
    - Creates files or folders for path on host if missing (depends on extension in path)
    - Mounts them to `/aicage/agent-config/` plus path in container
  - entrypoint.sh:
    - Takes subfolders of `/aicage/agent-config` and symlinks them to users home (which differs depending on host OS)
- `--share` arguments to `aicage`
  - python:
    - Mounts them to same path as on host (posix form if host is Windows)
  - entrypoint.sh:
    - Does not handle them

## Issues with current code

- 4 different ways to handle shared files/folders is way too much
- The current situation stems from a time when I was not sure what user will be used in container and how project-path
  shall be handled. Both are now pretty clear, with one dependency on host OS.
- We probably don't need the fallback `/workspace` anymore at all
- Then `entrypoint.sh` handles to many cases, I count 4 cases while `--share` values are not handled (might be correct
  but feels off)
- Handling so many values separately in `RunConfig` and `DockerRunArgs` feels off when both contain `env` and `mounts to
  store mounts and env-vars
- The current python code and entrypoint.sh still handles cases as if it's not clear what user will be used in
  container, but now this is clear.

## Basic idea

- The python code takes into account that it knows the user in the container
- A bit tricky could be mounting to paths which are below users-home. On Linux this results in user-home already
  existing (as folder above mountpoint target) when user (with home) shall be created by `entrypoint.sh`
  - if that is a problem, then we could mount all paths below users home to something like `/aicage/user-home/`+path in
    the container and let entrypoint create symlinks. We already kind of do that for git-related paths and agent-config
    paths. But we do it on a per-case basis not with a general: just symlink all subfolders to users-home. And if we do
    that then only for paths below users-home and for simplicity with just the relative path to users-home (meaning
    python does not calculate root-user or not part)
- Anything resulting in mounts or env-vars does not need to be separate in `RunConfig` and `DockerRunArgs`, unless there
  it's used for something else.
- Document the handling of mounts to containers in `aicage.wiki` for users as this is a key part of `aicage`.
- I am open to reasonable suggestions to change these ideas or to extend the scope of the change.
- Module idea: One possible idea that I have in mind is to refactor the handling of things like 'git-related paths',
  '--share paths', etc. into modules which implement a defined api - they all receive the same input and just output
  mounts and env-vars (or write them to an object passed to them). I'm not saying I want this now, but depending on how
  much we refactor this might be feasible

## Task Workflow

1. I am not sure if my above list of mount-use-cases and their handling is totally correct. The code is what matters so
   analyze the situation first
2. Check if code can be simplified, if parts can be merged.
3. Propose potential generic handling-solutions for the mount-use-cases, also list what falls outside it.
4. We interactively discuss possible solutions until I accept one.
5. Present me a clear implementation plan. This needs my approval.
6. Code autonomously. Make sure to respect coding guidelines and existing coding-style tests. Also respect
   `scripts/lint.sh`, this muss pass too.
7. I review your change and possibly tell you to commit in between

## Coding workflow

- Don’t forget to read `AGENTS.md` and `doc/python-test-structure-guidelines.md` and respect those rules.
- Always use the existing venv.

You shall follow this order:

1. Read documentation and code to understand the task.
2. Ask me questions if something is not clear to you.
3. Present me with an implementation solution; this needs my approval.
4. Implement the change autonomously including a loop of running-tests, fixing bugs, running tests.
5. Run linters, use `scripts/lint.sh` with active venv.
6. Present me the change for review.
7. Interactively react to my review feedback.
8. Do not commit any changes unless explicitly instructed by the user.
