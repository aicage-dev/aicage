# Review Notes

## `container_project_path()`

Move `container_project_path()` as it's only used once and not where it's defined.

## Split package `src/aicage/runtime/docker_args`

It's to large now. Possible split:

- Move all implementations of `Resolver` to one package
- Move code handling `Resolver` like `resolver.py` and code only used for that to a package
