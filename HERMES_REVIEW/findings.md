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

