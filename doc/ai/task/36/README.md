# Task 36: Support rootless Docker

## Summary

Investigate and add first-class support for running `aicage` with **rootless Docker**.

The goal is to improve the security model while preserving aicage's existing developer experience, especially around
bind-mounted workspaces and runtime user handling.

## Motivation

Today `aicage`assumes a traditional (rootful) Docker setup and dynamically creates a matching runtime user inside the
container.

Rootless Docker changes the security model and may allow `aicage` to reduce the impact of granting an AI agent access to
the Docker daemon while still supporting container orchestration.

The current runtime-user implementation needs to be reviewed to determine:

* which parts are still required,
* which parts should behave differently,
* and whether `aicage`  should automatically detect and adapt to rootless Docker.

See the [attached design notes](aicage-rootless-docker-issue.md) for the investigation topics and acceptance criteria.

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
