# Bulk Review: ba3a3f95..HEAD

Scope: 18 commits, 111 files changed.

This document captures issues found in a bulk review of all changes made since
(and including) commit `ba3a3f95`. Findings are grouped by severity.

## Warnings

### Dead code in `registry/agent_build/ensure.py`

`_build_needed_from_plan` (lines 143–146) and `_build_needed` (lines 149–183)
are defined but never called anywhere in the codebase. The newer `setup_plan`
function (line 101) supersedes both. Remove them.

### Missing `update_approved` threading in `ensure_image.py`

`ensure_image` (line 43) threads `update_approved` through `pull_image` and
`ensure_agent_image` but never passes it to `ensure_extended_image`. Extension
builds may internally pull a base image without any update-approval gate. If
this is intentional (extensions always rebuild without prompting), it should be
documented. Otherwise, `ensure_extended_image` should accept `update_approved`
too.

### Type alias inconsistency in textual `_execution_app.py`

`_ImageSetupOperation` in `src/aicage/runtime/menu/textual/_execution_app.py:14`
uses `Callable[[OperationReporter], None]`, but the same alias in
`runtime/menu/interaction.py:12` and `runtime/menu/textual/interaction.py:15`
uses `Callable[[OperationReporter | None], None]`. Align the definition in
`_execution_app.py` to match the Protocol.

### DRY violation in textual `_config_app.py`

`_ConfigResult` in `src/aicage/runtime/menu/textual/_config_app.py:35–38` is
identical to `ConfigSelectionResult` from `_interaction_types.py` (same fields,
same types). `ConfigApp` produces `_ConfigResult` which is immediately unpacked
and re-wrapped into `ConfigSelectionResult` in
`textual/interaction.py:27–30`. Use `ConfigSelectionResult` directly and remove
the redundant dataclass.

### Cross-package `_test_support` dependency in tests

Two test files import from a sibling subpackage's private test support:

- `tests/aicage/runtime/menu/test__none_interaction.py:11` imports from
  `.textual._test_support`
- `tests/aicage/runtime/menu/prompts/test_interaction.py:11` imports from
  `..textual._test_support`

Move `_build_context` and `_build_draft` to
`tests/aicage/runtime/menu/_test_support.py` (menu package level) and have
`textual/_test_support.py` re-export or delete its copy.

### Brittle `__wrapped__` pattern in textual tests

Eight call sites across `test__config_app.py` (×6), `test__execution_app.py`,
and `test__image_update_app.py` do:

```python
asyncio.run(cast(Any, app._accept).__wrapped__(app))
```

This bypasses the Textual `@work(thread=True)` decorator by directly invoking
the unwrapped method. If the decorator changes or is removed, every call silently
breaks. Extract a helper like `_run_work_sync(app, method_name)` to centralise
the pattern.

### Missing tests in `runtime/test_image_setup.py`

The test for `confirm_image_update → True` exists, but there is no test for the
`False` (reject) path. When the user rejects an update, `prepare_image` should
still pass `update_approved=False` to `ensure_image`. This behaviour is
untested.

### Missing assertions in `menu/test__none_interaction.py`

`ConfigureRunTests.test_configure_run` (lines 21–41) mocks
`select_agent_image` and `apply_mount_preferences` but never asserts that
`draft.apply_selection`, `_persist_docker_args`, or `_persist_shares` were
called. These are key side effects in the source.

### Missing test for successful execution path

`tests/aicage/runtime/menu/textual/test__execution_app.py` only tests the error
path (`test_run_execution_exits_with_error`). There is no test for the happy
path where `_run_execution` completes successfully and calls
`call_from_thread(self.exit, None)`.

## Nits

### Redundant `elif` in `ensure_image.py`

`src/aicage/registry/ensure_image.py:56` — the `elif` condition is the exact
complement of the preceding `if`. Simplify to `else`.

### Defensive `or ""` in `image_selection/selection.py`

`src/aicage/registry/image_selection/selection.py:43` — the `or ""` fallback
masks a condition that should be impossible at this point. Remove or add an
assert.

### `ConfigSelectionResult` visibility

`src/aicage/runtime/menu/_interaction_types.py:6–9` — `ConfigSelectionResult`
is only used inside the `runtime.menu` package. Per visibility rules it should
be package-private (`_ConfigSelectionResult`).

### Implicit string concatenation in `_confirm.py`

`src/aicage/runtime/menu/prompts/_confirm.py:112` — `"…available. " "Pull now?"`
is an implicit concatenation. Merge into a single f-string.

### Redundant binding in `image_update_confirm_screen.py`

`src/aicage/runtime/menu/textual/views/image_update_confirm_screen.py:10–13` —
the `ctrl+c → cancel` binding is already inherited from `TextualApp.BINDINGS`.
Remove the redundant entry.

### Visibility rule gap in `test_visibility.py`

`tests/repo_rules/test_visibility.py:216–237` — `_iter_private_symbol_imports`
only checks `ast.ImportFrom` (`from module import _name`). A bare
`import _private_module` (`ast.Import`) would not be caught.

### Incomplete assertion in `test__execution_app.py`

`tests/aicage/runtime/menu/textual/test__execution_app.py:36–44` —
`killpg_mock.assert_called_once()` does not verify arguments. Should be
`assert_called_once_with(os.getpgrp(), signal.SIGINT)`.

### Stale redirect URL in `README.md`

`README.md:115` — the homepage URL 301-redirects to a canonical path with a
`/`. The link works but adds a redirect hop. Consistent with
`config/agent-build/agents/agy/agent.yml:5`.
