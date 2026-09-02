# Findings

Format:
- Severity: `high` / `medium` / `low`
- Confidence: `high` / `medium` / `low`
- Affected: file:line
- Explanation
- Suggested fix

## 1. Registry digest lookup does not use authenticated pull flow for private/unauthenticated registries

Severity: medium
Confidence: high
Affected:
- `src/aicage/registry/digest/_auth.py`
- `src/aicage/registry/digest/_registry.py`
- `src/aicage/registry/digest/remote_digest.py`

Explanation:
Remote digest resolution uses anonymous HEAD requests with optional bearer token exchange from `www-authenticate`.
This works for public GHCR/Docker Hub images, but for private registries or mirrors that require
credentialed pulls, digest checks can fail even when `docker pull` would succeed with stored credentials.
This can cause false-negative update prompts or unnecessary CONFIRM_PULL decisions.

Suggested fix:
Document that remote digest resolution requires public image visibility. Optionally add a fallback that
skips remote digest resolution when anonymous access returns 401/403, treating the image as pull-required.

## 2. Cosign verification path bypassed for local builds without public remote verification

Severity: high
Confidence: medium
Affected:
- `src/aicage/registry/_image_pull.py`
- `src/aicage/registry/ensure_image.py`

Explanation:
`pull_image()` resolves a verified digest and verifies cosign before pulling.
For local/custom builds, `ensure_image()` does not verify signatures at all.
An attacker who can push to the local Docker daemon or replace `aicage-dev/aicage-image-*` images
can achieve code execution without cosign validation.

Suggested fix:
Introduce optional signature verification for local images, or clearly document that cosign guarantees
only apply to remote builtin images. Enforce repository namespace restrictions for local builds.

## 3. Project config YAML lacks integrity protection

Severity: medium
Confidence: high
Affected:
- `src/aicage/config/config_store.py`
- `src/aicage/config/_file_locking.py`

Explanation:
Project config is stored under `~/.aicage/projects/*.yml` as plaintext YAML with file locking only.
There is no MAC or signature. An attacker with local write access can modify mounts, docker args,
or base image selection, causing the next `aicage` run to mount arbitrary host paths or use
a tampered image ref.

Suggested fix:
Add an optional integrity check, or at minimum warn when project config permissions are too open.
Restrict sensitive fields if community threat models include local attackers.

## 4. Hard-coded cosign image digest can become stale, and fallback is not version-pinned

Severity: low
Confidence: high
Affected:
- `src/aicage/constants.py`

Explanation:
`COSIGN_IMAGE_REF` is pinned to a digest, which is good. But `VERSION_CHECK_IMAGE` is a tag,
so version-check image freshness depends on mutable tags.

Suggested fix:
Pin `VERSION_CHECK_IMAGE` to a digest as well, or add digest verification for that image too.

## 5. Subprocess command construction uses list args, but merged Docker args are shlex-split

Severity: medium
Confidence: high
Affected:
- `src/aicage/docker/run.py`
- `src/aicage/runtime/run_args.py`

Explanation:
`merged_docker_args` is a freeform string from user config or CLI. It is split with `shlex.split`
and extended into the docker argv list. Because it is not passed through a shell, classic shell
injection is avoided, but shlex still interprets quotes and escapes. A crafted string like
`'-v /host:/container --rm'` could inject unexpected tokens if user-edited config contains
unbalanced quotes. The CLI help says docker args are forwarded verbatim, but the current path
does not preserve verbatim argv boundaries.

Suggested fix:
Capture docker args as a list from the start, or document and validate that quotes/escapes are
interpreted. Consider rejecting known-dangerous flags such as `--privileged` unless explicitly enabled.

## 6. Home-directory mount guard can be bypassed on Windows/WSL path forms

Severity: medium
Confidence: medium
Affected:
- `src/aicage/runtime/docker_args/resolve/resolver.py`
- `src/aicage/paths.py`

Explanation:
`_validate_home_mount_safety()` compares resolved `Path` values against `Path.home()` on the host.
On Windows/WSL, Docker mounts may use `/mnt/c/Users/...` style container paths derived from
`container_project_path()`, but host paths are still resolved through Windows path parsing.
Edge cases with symlinks, `/`, and `\\` prefixes may slip past exact `Path` equality checks.

Suggested fix:
Add explicit tests for WSL/Windows-style home path normalization. Consider normalizing both sides
with `resolve()` and `as_posix()` before comparison.

## 7. TTY allocation is disabled only when `--stdio` is set; piped agent I/O may still get Docker TTY

Severity: low
Confidence: high
Affected:
- `src/aicage/cli/_parse.py`
- `src/aicage/docker/run.py`
- `src/aicage/docker/execution/cli.py`

Explanation:
`--stdio` maps to `docker run -i`. But `aicage` also supports piping stdin/stdout from the parent
process in menu=none mode without `--stdio`. In that case, Docker still allocates a TTY, which can
break protocol framing for some agent CLIs.

Suggested fix:
Detect non-TTY parent stdio and default to `-i`, or require `--stdio` whenever stdin is not a TTY.

## 8. Local image digest cleanup can race with concurrent `aicage` runs

Severity: low
Confidence: medium
Affected:
- `src/aicage/docker/query.py`
- `src/aicage/registry/agent_build/ensure.py`
- `src/aicage/registry/extension_build/ensure.py`

Explanation:
`cleanup_old_digest()` removes images by digest after pull/build. Concurrent runs can both read
the same old digest, then one removes an image the other still needs. Build records reduce rebuilds,
but do not serialize cleanup.

Suggested fix:
Use per-repo advisory locking around build/pull/cleanup, or make cleanup idempotent by checking
referrers before `docker image rm -f`.

## 9. README and docs describe `--docker` and socket behavior, but socket enablement logic is incomplete in docs

Severity: low
Confidence: high
Affected:
- `README.md`
- `src/aicage/runtime/docker_args/resolvers/docker_socket.py`

Explanation:
README documents `--docker` and Docker socket sharing. `docker_socket.py` only mounts the socket
when `mounts_cfg.docker` is true or CLI flag is set. But saved config prefill in
`run_config_draft.py` sets `mounts_cfg.docker = True` when `--docker` is used, while UI overview
does not appear to persist `--docker` back into docker args. This may cause inconsistent behavior
between CLI-first and UI-first flows.

Suggested fix:
Document that socket sharing must be enabled via config/UI. Ensure UI enables `mounts_cfg.docker`
and that the resolver always respects persisted config.

## 10. Build log paths use image refs with unsafe characters without additional sanitization

Severity: low
Confidence: low
Affected:
- `src/aicage/registry/_logs.py`
- `src/aicage/registry/extension_build/_logs.py`
- `src/aicage/registry/agent_build/_logs.py`

Explanation:
Log paths are derived from image refs and agent names. Some sanitization exists, but image tags
can still contain characters that are problematic on some filesystems. If registry or user-defined
tags contain unusual characters, log path creation can fail.

Suggested fix:
Use stable identifiers from config/state rather than raw refs for log filenames.
