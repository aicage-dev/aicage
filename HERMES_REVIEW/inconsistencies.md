# Inconsistencies

## aicage vs aicage.wiki

- README links to wiki for full docs, but wiki does not describe Linux-only integration constraints
  in the same detail as `DEVELOPMENT.md`.
- Wiki docs for Docker args and host networking should clarify that `--docker` requires matching
  config/UI state; current README wording is looser than implementation in
  `src/aicage/runtime/docker_args/resolvers/docker_socket.py`.

## aicage vs related repos

- `../aicage-image`, `../aicage-image-base`, `../aicage-image-util` are referenced as image sources,
  but no local source checkout or submodule linkage is present; only built images are consumed.
- Fork constants in `src/aicage/constants.py` use `aicage-dev/*` repositories. If those fork repos
  do not mirror extension/base config layouts, custom-sample guidance in README may break.

## Config docs vs code

- `README.md` shows `--share <path>` as repeatable; code supports repeatable `--share` but also
  extension-requested shares via prompts.
- `README.md` shows `--config remove [<agent>]`; CLI parser allows `--config remove` without agent,
  and removal prints "Project config removed" even when nothing existed.
