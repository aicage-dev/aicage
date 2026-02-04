# 26 - Analysis of situation

## Current env-vars used by entrypoint.sh

entrypoint.sh reads these env vars (directly or via defaulting):

AICAGE vars

- AICAGE_WORKSPACE
- AICAGE_ENTRYPOINT_CMD
- AICAGE_USER
- AICAGE_UID
- AICAGE_GID
- AICAGE_HOST_USER

System vars used as fallbacks

- USER
- UID
- GID
- HOME (set by entrypoint)
- PATH (appended to)

There’s also an internal shell variable WINDOWS_HOST_HOME_POSIX computed from AICAGE_WORKSPACE, but it’s not an env var.

## What it should do

What the entrypoint.sh needs is:
- AICAGE_WORKSPACE: The project path on host (CWD) in posix form
  This can be by a symlink to a mount, it does not need to be a mount directly
- AICAGE_ENTRYPOINT_CMD
- AICAGE_HOST_USER: What the user on host is
- AICAGE_UID: only needed for Linux hosts
- AICAGE_GID: only needed for Linux hosts
- AICAGE_HOME: what the posix path of user home on host is
- AICAGE_HOST_IS_LINUX: to know if host is linux or not

The python code on host does:
- for mounts outside user-home: mount them to same path (in posix form if on Windows)
- for mounts under user-home: mount them to `/aicage/user-home` with same sub-path as on host relative to user home
  - example:
    - host-path: C:\Users\<user>\.gitconfig
    - mountpoint: /aicage/user-home/.gitconfig

The entrypoint.sh in containers does:
- User: On Linux host, create user with UID and GUID. On Windows host, use root
- Then for each mount matching `/aicage/user-home/{path}`:
  - for Linux host:
    - create a symlink from `${AICAGE_HOME}/{path}` to the mount
  - for Windows host:
    - create a symlink from `${AICAGE_HOME}/{path}` to the mount
    - create a symlink from `/root/{path}` to the mount
- switch to user (if on Linux host) with the AICAGE_WORKSPACE as current working directory

With this we achieve:
- working dir matches host-path (posix for for Windows hosts)
- all mounts have same relative path to AICAGE_WORKSPACE
- the user in the container has all mounts under user home in his home, same as on the host

## Affected code

- `entrypoint.sh` in project `../aicage-image-base`
- `bats` tests in `../aicage-image-base/tests/smoke/default/*entrypoint*.bats`
- python code and tests in `.` (the `aicage` repo)
- Task documentation in `./doc/ai/task/26` which might still contain other information
- User documentation in `../aicage.wiki/` and Markdown files in the `aicage` repo

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
