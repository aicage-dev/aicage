# Task 25 — Add `aicage` Share Option

## Goal

Add a CLI option that allows users to define additional shared mounts into the container.

## Scope

- Code: new CLI parsing, config integration, and docker run assembly.
- Docs/tests/examples: document the option and add tests.

## Definitions

- Share: extra bind mount from host to container for a single run.
- Read-only share: a share mount that must not allow writes inside the container.

## Requirements

- Option name: `--share`.
- Repeatable: users can pass it multiple times.
- Accept values:
  - `HOST` (defaults to container path `HOST` and rw)
  - `HOST:ro`
- If `:ro` is present, use a read-only mount.
- If `HOST` is relative, resolve relative to the current working directory.
- Container destination path always matches the resolved host path (posix conversion on Windows).
- If the resolved host path does not exist, create it (file if it has a suffix, otherwise a directory).
- If the resolved host path exists but is not a file or directory, fail with a clear error.
- If the same host path is already mounted (project path or existing mounts), skip it.

## Implementation steps

1. Parse CLI
   - Add a repeatable `--share` option to CLI parsing.
   - Store raw values for further resolution.
2. Resolve shares
   - Parse each share string into host path and readonly flag.
   - Container path always mirrors the resolved host path.
   - Use `Path` and `PurePosixPath` for host and container paths respectively.
   - Resolve relative paths per requirements.
3. Add to run config
   - Integrate into runtime config by adding to mounts list.
   - Do not change persisted project config unless explicitly requested.
4. Update run args
   - Ensure the docker run builder includes the share mounts.
5. Tests
   - Add unit tests for parsing and resolution.
   - Add unit tests that assert the mounts are added with correct paths and flags.
   - Add a test that verifies duplicates are skipped.
6. Docs
   - Document the option in the appropriate docs.

## Acceptance criteria

- `aicage run --share` mounts are correctly included in `docker run` args.
- Read-only handling uses readonly mount semantics.
- Relative host paths resolve to the current working directory.
- Container destinations match resolved host paths.
- Duplicate mounts are skipped.
- Tests pass and linting passes.

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
