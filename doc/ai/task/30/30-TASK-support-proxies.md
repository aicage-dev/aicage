# Task 30 — Support proxies

## Problem

The host running `aicage` might be behind a proxy.

### Network needed during image preparation

`aicage` relies on a working network connection (to verify if local images are up to date, to pull or build images).
We recently made an effort to avoid hard crashes during image preparation (when images are already present locally then
don't exit when update-checks fail due to network). But for normal process network is assumed, but proxies are quite
common in corporate networks.

Those network accesses include:

- REST calls to (GitHub) image registry.
- Docker command calls (pull, build, etc.)

### Network needed in container to run agent with remote LLM

The coding agent might be able to reach the LLM when running bare-metal on the host but with `aicage` that agent is
running in a docker container.

## Other documents

I discussed this with ChatGPT in a browswer session resulting in these 2 documents:

- doc/ai/task/30/aicage-network-proxy-analysis.md
- doc/ai/task/30/aicage-network-proxy-task-instructions.md

Frankly I do not understand the 2 documents and think they are rather bloated. By maybe they help you.

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
