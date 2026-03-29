# Task 34 - Custom share per extension

## Tasks

This has one main task and a few side-tasks

- main task: Custom share per extension
- side-task: `--config info` does not need user-facing `info`. With `--config` alone, print the info.

Maybe do the small side-task(s) first.

## Custom share per extension

I frequently use extensions or tools, which more or less require (or often require) an additional share with host.

Examples:

- `maven`: Sharing `~/.m2` is often feasible, although I'm not sure about sharing Windows m2 into Linux containers.  
  Is preinstalled on aicage images.
- `gh`: To run GitHub actions locally and more. Stores its login locally below user home, without PAT must be used.  
  Installed as aicage custom extension `../aicage-custom-samples` (aicage reads it from `~/.aicage-custom`, a symlink
  to `../aicage-custom-samples`)

So my idea is to let extensions trigger extra shares by aicage, requiring user confirmation as other shares, maybe in
a separate "extension x suggests/wants these shares ok" prompt for clarity.  
As extensions are user written (mine are just samples - the ones I use), this should if possible not force user to write
python as now the extensions are pure shell/bash.

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
