# Task 31 - Tune questions to user

This task has several parts, all related to questions aicage asks a user.

## Part 1: Tune git-config-mount question

Currently, aicage asks only one yes/no question for 3 internal mount-options (gitconfig, gnupg, ssh).  
This was changed to one question only a while ago to reduce total question count.  
Example:

```shell
Enable Git support in the container by mounting:
  - Git config (name/email): /home/stefan/.gitconfig
  - GnuPG keys (for Git signing): /home/stefan/.gnupg
Proceed? [Y/n]
```

But actually this is reducing options to users. Can you please changes this to something like a list where user can
select `1,2,3` while keeping a default where if user just presses Enter then the same default as now is applied?

## Part 2: Add optional '-y/--yes' CLI argument

If passed, all questions to user simply take the default. An actual output to user of the question is not needed then.
Maybe an info text could be presented to user - but we must log the choices made for sure. It's your choice about info
text to user - the intended use-case is scripted use anyway so I don't know if info-text is needed.

## Part 3: Add integration tests for part 1 and part 2, use `--yes` to simplify integration tests

Both part 1 and part 2 demand integration-tests.

Plus the `--yes` option might come handy in existing integration-tests as it might simplify test runs where we have to
set up an aicage-config first. Your choice per case if it's worth changing existing tests.

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
