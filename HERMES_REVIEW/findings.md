# Findings

Format:
- Severity: `high` / `medium` / `low`
- Confidence: `high` / `medium` / `low`
- Affected: file:line
- Explanation
- Suggested fix

## 7. TTY allocation is currently controlled by `--stdio`; future auto-detection planned

Severity: low
Confidence: high
Affected:
- `src/aicage/cli/_parse.py`
- `src/aicage/docker/run.py`
- `src/aicage/docker/execution/cli.py`

Explanation:
`--stdio` was added to support non-TTY callers such as IDE plugins, where Docker should use `-i` instead of `-it`.
Evidence from `../aicage.wiki/ide-plugins/jetbrains/cc-ui/log/codex-20260902-172748.log` shows the plugin
invokes `aicage` with stdin/stdout/stderr all non-TTY. The current code relies on the caller to pass `--stdio`
explicitly in such cases.

Planned change:
Replace explicit `--stdio` with auto-detection based on whether stdin is a TTY. After that change,
`--stdio` will be removed or kept only as a deprecated no-op. This removes the need for plugin shims
to pass the flag explicitly.

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
