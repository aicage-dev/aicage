# Task 32 - Improve mounts in user home

## Situation

`aicage` currently treats mounts to its containers differently when the mounted dir/file is below user-home on host.

Then it does not mount them to the equivalent of the path on host but rather:

1. mounts them to a dedicated folder `/aicage/user-home`
2. the entrypoint script (see `../aicage-image-base/scripts/entrypoint.sh`) in containers creates the user (with
user home)
3. then the entrypoint.sh symlinks those mounts into user home.

If those mounts were directly mounted to the target path, then the user home would already exist before the entrypoint
creates the user. And this would hinder the default user setup on Linux.

## Problem

While this works in all cases, I keep seeing tools (coding agents) using the real path (of the mount point) not the
virtual path of the symlink.

And sometimes this has minor side effects - but overall it's plain ugly when we promise/try to provide the same
situation as on host.

## Solution/Task

I want you to hard analyze the alternative: mount directly to target path and adapt user creation:

- user home will/might already exist upon user creation - owned by root. This must be worked around.
- whatever the linux distro does when setting up a user home will likely not work the same when the home folder already
  exists. Again, this must be worked around.

What I basically want is a valid option where we can mount to paths in containers user home and the entrypoint handles
things so user-home is equals to what it would be now.

## Task workflow

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
