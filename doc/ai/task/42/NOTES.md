# Notes from 2026-11-26

## Add `--ssh` and `--gpg`?

Before task 42 SSH/GPG was included in the CLI args for git. Now it's not (or should not be).
When adding CLI args to `aicage` we must check that Docker CLI does not use the same ones.
