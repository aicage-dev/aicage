# Architecture Summary

## Project overview

`aicage` is a Python CLI that runs AI coding assistants inside Docker containers.
The CLI resolves configuration, builds or pulls container images, and then executes
the agent container with appropriate mounts, environment variables, and Docker args.

## Main execution flow

1. `src/aicage/cli/entrypoint.py:main` parses CLI args and creates a runtime interaction.
2. It loads run configuration via `src/aicage/config/runtime_config.py:load_run_config`.
3. It builds Docker run arguments via `src/aicage/runtime/run_args.py:build_run_args`.
4. It prepares the image via `src/aicage/runtime/image_setup.py:prepare_image`.
5. It either prints the docker command or runs it via `src/aicage/docker/run.py`.

## Configuration layers

- Built-in agents/bases/extensions live under `config/`.
- User project config lives under `~/.aicage/projects/...`.
- Custom extensions/agents/bases live under `~/.aicage-custom/`.
- Schema validation uses JSON Schema under `config/validation/`.

## Image management

- Remote digests are resolved via unauthenticated HEAD requests to GHCR/Docker Hub.
- Official images are verified with cosign against GitHub Actions OIDC identities.
- Local builds use Docker build with caching via build records stored as YAML.

## Menus/UI

- Textual UI, simple prompts, or no interaction can be selected.
- All menu modes implement `RuntimeInteraction` protocol.

## Inspected scope

- All Python source under `src/aicage/`.
- Tests under `tests/`.
- Config schemas, Dockerfiles, shell scripts under `config/` and `scripts/`.
- README, DEVELOPMENT, pyproject, requirements.
- Related documentation in `../aicage.wiki`.
- Related repos `../aicage-image`, `../aicage-image-base`, `../aicage-image-util`, `../aicage-custom-samples` for interface context.
