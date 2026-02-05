# Task 27 — Don't rely on path with extension equals file

## Intended change

For `agent_path` and `--share` mounts aicage creates files/folders on host solely on the path basename having a dot.
This is utterly brittle.

Instead, we should extend `agent_path` to have 2 child lists: `files` and `folders` (or file/folder or files/dirs ...
please change these 2 names to match best naming practice). Then we can partially rely on default docker behavior (which
imho is to create folder if missing on host) and only for file mounts create an empty file.

For `--share` we would no longer do such a thing meaning we let docker handle it. And the user: if it's a file, and it
does not exist yet on host ... well he will find out and create a blank file himself sooner or later.

## Affected repos

- repo `aicage-image` in `../aicage-image` where builtin agents are defined.
  - All `agents/*/agent.yml`
  - `doc/validation/agent.schema.json` used for validation of `agent.yml` files
- repo `aicage` in current working dir
  - All `config/agent-build/agents/*/agent.yml`
  - `config/validation/agent.schema.json` used for validation of `agent.yml` files, potentially equals to the one from
    repo `aicage-image`
  - Possible documentation in '*.md' files
  - The code handling/parsing `agent_path` from `agent.yml` files
- repo `aicage-custom-samples` in `../aicage-custom-samples`
  - `agents/forge/agent.yml`
  - `validation/agent.schema.json`
- repo `aicage.wiki` in `../aicage.wiki`: The user facing documentation for `aicage`
  - `CLI-Options.md`
  - `Customization-Agents.md`

This list might not be complete, extend it at your will.

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
