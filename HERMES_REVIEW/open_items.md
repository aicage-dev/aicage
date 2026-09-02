# Open Items

Unverified concerns and future test tasks that are not confirmed defects but may deserve follow-up.

## Windows/WSL home-directory mount safety

- Affected: `src/aicage/runtime/docker_args/resolve/resolver.py`, `src/aicage/paths.py`
- Note: `_validate_home_mount_safety()` compares resolved `Path` values against `Path.home()` on the host.
- Concern: On Windows/WSL, path normalization, symlinks, and `/mnt/...` forms may behave differently than on Linux.
- Suggested next step: Test on Windows/WSL. If issues appear, normalize both sides with `resolve()` and `as_posix()` before comparison.
