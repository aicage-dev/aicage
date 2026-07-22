# Code Review: Changes Since Tag 1.4.4

Reviewed changes: 120 files, +2809/-1523 lines.
Focus: Task 38 (Menu/Process Boundary), visibility enforcement, Textual UI split.

## Summary

The core change introduces a `RuntimeInteraction` Protocol boundary that cleanly
separates menu/UI concerns from runtime execution logic. The old monolithic
`entry.py` Textual app is split into phase-specific apps (`_config_app`,
`_execution_app`, `_image_update_app`). File renames enforce private-by-default
visibility. A new repo rule test enforces visibility conventions.

## Issues (Must Fix)

1. `_ConfigSelectionResult` is private (`_`-prefixed) but appears in the public
   `RuntimeInteraction` Protocol signature. External callers (`runtime_config.py`,
   `image_setup.py`) use it. Either rename to `ConfigSelectionResult` or document
   the trade-off.
   - `src/aicage/runtime/menu/interaction.py:20`

2. `SimpleInteraction.execute_image_setup` uses raw
   `Callable[[OperationReporter | None], None]` instead of the centralized
   `ImageSetupOperation` alias. Defeats the purpose of `_interaction_types.py`.
   - `src/aicage/runtime/menu/prompts/interaction.py:67-69`

3. `test_main_config_remove` and `test_main_config_remove_with_agent` don't mock
   `create_runtime_interaction`, causing real `TextualInteraction` (Textual App) to
   be instantiated unnecessarily. Should be mocked like the other 4 tests.
   - `tests/aicage/cli/test_entrypoint.py:175,191`

4. `test_public_symbols_are_used_outside_package` is permanently
   `@expectedFailure` with no tracking issue. New violations can slip in
   undetected. Add `TODO(#issue)` or convert to a proper skip with a deadline.
   - `tests/repo_rules/test_visibility.py:129`

5. `local_digest` is fetched before the `should_pull` guard but only used
   post-pull in `cleanup_old_digest`. Move the fetch after the guard to avoid a
   wasteful Docker API call when no pull is needed.
   - `src/aicage/registry/_image_pull.py:18`

## Suggestions (Nice-to-Have)

1. `create_runtime_interaction(menu: str)` uses raw strings. A
   `Literal["textual", "none"]` or enum would make valid options explicit. Unknown
   strings silently fall through to `SimpleInteraction` — should they error?
   - `src/aicage/runtime/menu/interaction.py:34-38`

2. `del agent` in `configure_run` is unusual. If `agent` is intentionally unused,
   add a comment or drop from the Protocol signature.
   - `src/aicage/runtime/menu/textual/interaction.py:23`

3. `_extended_image_name` and `_default_extended_image_ref` are duplicated between
   `overview_selection.py` and `extensions/handler.py`. Extract to a shared helper.
   - `src/aicage/config/overview_selection.py:70-76`
   - `src/aicage/registry/image_selection/extensions/handler.py:73-79`

4. `yield from ()` is correct but unusual. A plain `return` or a brief comment
   would improve clarity.
   - `src/aicage/runtime/menu/textual/_image_update_app.py:14`

5. `ExecutionApp` and `ImageUpdateApp` both share sub_title `"container setup"`.
   Consider differentiating for better user context.

6. Tests assert on `__class__.__name__` strings. Fragile under renames — consider
   behavioral checks or `@runtime_checkable`.
   - `tests/aicage/runtime/menu/test_interaction.py:12-25`

7. Stale `overview/` and `screens/` directories under
   `src/aicage/runtime/menu/textual/` contain only `__pycache__` — remove them.

8. `_persist_docker_args` and `_persist_shares` have branching logic with no
   dedicated tests.
   - `src/aicage/runtime/menu/_none_interaction.py:80-95`

9. `test_src_has_no_all` uses text search for `__all__` — should use AST for
   consistency with the rest of the file.
   - `tests/repo_rules/test_visibility.py:17`

10. Old structured logging from prompts is gone; `SimpleInteraction` doesn't add
    equivalent logging. Consider restoring observability.
    - `src/aicage/config/runtime_config.py`

## Strengths

- **Clean Protocol-based boundary.** `RuntimeInteraction` (3 implementations:
  `SimpleInteraction`, `_NoneInteraction`, `TextualInteraction`) cleanly decouples
  UI from runtime. The registry/config layer has zero imports from
  `aicage.runtime.menu` — confirmed by grep.

- **`runtime_config.py` simplification.** Dropped from ~130 lines of mixed concerns
  to 72 lines of pure orchestration. Dead helpers (`_persist_docker_args`,
  `_persist_shares`, `_execute_image_setup`, `_image_setup_needed`,
  `_setup_run_config`) removed.

- **Missing extensions flow dramatically simplified.** Eliminated TTY dependency,
  cross-project YAML scan, and `yaml_loader` dependency from the module. Now:
  log warning, auto-remove missing extensions, update `image_ref` in-place.

- **File renames are thorough.** `yaml_loader` → `_yaml_loader`, prompt modules to
  `_`-prefixed — all 6+ consumer files updated, no stale imports remain.

- **Visibility enforcement test is comprehensive.** 9 test cases cover `__all__`,
  `__init__` functions, private imports, runtime imports, and unused symbols.
  - `tests/repo_rules/test_visibility.py`

- **Test mirroring is correct.** Every src rename has a matching test rename. Test
  names mirror src module/method structure per AGENTS.md conventions.

- **Textual split is well-executed.** Monolithic `entry.py` → 4 focused apps
  (`_textual_app`, `_config_app`, `_execution_app`, `_image_update_app`) +
  facade (`interaction.py`). Old code fully deleted with no stale references.

- **`image_setup.py` is a clean orchestration point.** Reads like pseudocode:
  plan → check → approve → execute. No UI logic leaks in.

- **`_NoneInteraction` is architecturally correct.** Auto-accepts all defaults,
  selects all mounts, calls operation directly. "Not a special process path"
  principle.

- **All lint suppressions are justified** with inline comments per AGENTS.md
  rules. Every `nosec` annotation explains why the security warning is acceptable.

- **All tests pass** and the diff is net negative (-1523 lines removed vs +2809
  added = codebase simplified overall).
