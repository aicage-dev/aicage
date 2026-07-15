# Task 37 Status

## Current state

The interactive config UI now follows the explicit menu mode:

- `aicage <agent>` defaults to `--menu textual`
- `aicage --menu simple <agent>` uses the classic line-based prompt flow
- `aicage --menu none <agent>` skips interactive menus and uses defaults

The persistence contract remains:

1. Load existing config for current folder and agent.
2. Build one in-memory `RunConfigDraft`.
3. Let the UI mutate only that draft.
4. Save the project config once after final acceptance.
5. Cancel must not persist partial state.

## Current UI architecture

### Runtime menu layout

Interactive runtime flows now live under `src/aicage/runtime/menu/`.

Current structure:

- `src/aicage/runtime/menu/prompts/`
  - classic non-Textual prompt flow
- `src/aicage/runtime/menu/textual/`
  - Textual-based interactive config UI
- `src/aicage/runtime/menu/default_base.py`
  - shared `resolve_default_base()` helper

Important entrypoints:

- Textual UI public entry:
  - `src/aicage/runtime/menu/textual/entry.py`
- Textual UI is used from:
  - `src/aicage/config/runtime_config.py`

### Main Textual overview

Implemented with Textual in inline mode.

Current main overview sections:

- `Base`
- `Extensions`
- `Docker Args`

Below the top row there is an access area:

- `Bind Mounts`
  - built-in git-support bind mounts
  - extension-provided bind mounts for selected extensions
  - custom bind mounts
  - compact `+` add button
- `Docker`
  - currently contains `Docker socket`

Relevant files:

- `src/aicage/runtime/menu/textual/_app.py`
- `src/aicage/runtime/menu/textual/overview/view.py`
- `src/aicage/runtime/menu/textual/overview/_shares.py`
- `src/aicage/runtime/menu/textual/_mount_display.py`
- `config/textual/overview/app.tcss`

### Current package shape

The refactor away from one huge `_app.py` has started but is not complete.

Current larger modules:

- `src/aicage/runtime/menu/textual/_app.py`
  - 200 lines
- `src/aicage/runtime/menu/textual/overview/view.py`
  - 191 lines
- `src/aicage/runtime/menu/textual/screens/host_access_confirm_screen.py`
  - 155 lines
- `src/aicage/runtime/menu/textual/services/_share_support.py`
  - 139 lines

This is notably better than the earlier single-file concentration, but there is still room to split more view-specific
and screen-specific logic if needed.

## Current behavior details

### Base / Extensions / Docker Args

- Base uses its own screen.
- Extensions uses its own screen.
- Docker arguments are edited in `screens/docker_args_screen.py`.
- Extensions still uses checkbox rows.
- Extensions `Clear` clears the live checkbox state in place and does not exit.
- Extensions now handles the no-custom-extensions case without crashing.
- When no optional extensions are available:
  - the screen shows a short empty-state explanation
  - it shows the sample repo clone command in a read-only command box
  - actions are reduced to `Copy Command` and `Back`
- `Copy Command` now tries system clipboard tools first and only falls back to Textual's OSC 52 clipboard support.
  - Linux:
    - `wl-copy`
    - `xclip`
    - `xsel`
  - macOS:
    - `pbcopy`
  - Windows:
    - `clip`
- Important implementation detail:
  - Linux clipboard helpers such as `xclip` may stay alive to own the clipboard
  - the Textual screen therefore uses a short timeout-bounded `Popen(...)` path instead of blocking on
    `subprocess.run(...)`

### Bind mounts

User-facing wording in the Textual menu should now be thought of as `Bind Mounts`, not `Shares`.

Behavior:

- Built-in git-support bind mounts are shown first in a `SelectionList`.
- Extension-provided bind mounts for selected extensions are shown together with those built-in items.
- Each resolved extension bind mount is shown on its own row.
- Rows from the same extension still toggle and persist as one extension-level group.
- Custom bind mounts are shown after them in the same list.
- Built-in git-support items still toggle directly in the list and do not open a popup.
- Selecting a custom bind mount opens the editor popup prefilled with that value instead of removing it directly.
- The custom bind mount editor supports removal through a dedicated `Remove` button.
- The editor also supports read-only mounts through a `Read-only` checkbox.
- The editor includes a `DirectoryTree`, but it is currently always rooted at `/`.
- The tree is intentionally treated as a helper for choosing a fresh path, not as a context-aware browser rooted near the
  current value.

Current list-display behavior:

- built-in and extension-provided items render as `<prefix>: <path>`
- custom read-only items render as `Read-only: <path>`
- custom read-write items render with a blank padded prefix column so all list rows align visually
- the prefix/label formatting now lives centrally in `src/aicage/runtime/menu/textual/_mount_display.py`

Current built-in-style labels:

- `Git config`
- `Git root`
- `SSH`
- `GnuPG`
- `Extension <id>`
- `Read-only`

Known limitation:

- very long bind-mount rows are still single-line `SelectionList` entries and will truncate once the overview shell
  reaches the viewport cap

### Docker socket

Docker socket is no longer in the Docker arguments screen.

Behavior:

- It lives in the overview `Docker` list.
- It is persisted through the same final accept flow as the git-support bind mounts.

### Host access confirmation popup

There is now a unified confirmation popup:

- title:
  - `Confirm Host Access`
- section 1 when needed:
  - `Docker support`
- section 2 when needed:
  - `Git support`
- section 3 when needed:
  - `Extension bind mounts`

Confirmation rules:

- only include items whose persisted startup value was not `True`
- and which are currently `True` when overview `OK` is pressed
- sections with nothing to confirm are hidden
- if nothing needs confirmation, the popup is skipped
- deselecting in the popup persists that item as `False`
- extension-provided bind mounts are only shown when the selected extension newly enables them relative to stored state
- multiple rows from one extension still act as one grouped toggle
- the popup now clears the initial per-list highlighted row state when focus starts on `OK`

Relevant file:

- `src/aicage/runtime/menu/textual/screens/host_access_confirm_screen.py`
- `config/textual/overview/app.tcss`

Current width behavior:

- the host-access confirmation popup is now narrower than the generic sub-screen shell
- it uses a dedicated `confirm_screen_shell` class instead of the shared wide `.screen_shell`
- intent:
  - keep it visually closer to the overview width
  - avoid changing the width of unrelated sub-screens

### Bind mount editor popup

The old early PoC popup has been replaced with a more useful editor screen.

Current behavior:

- title:
  - `Add Bind Mount`
  - or `Edit Bind Mount` for an existing custom item
- text input:
  - `Host path`
- read-only toggle:
  - `Read-only`
- filesystem helper:
  - `DirectoryTree`
- buttons:
  - `Cancel`
  - optional `Remove`
  - `OK`
- pressing `Enter` in the `Host path` input accepts like `OK`

Important current implementation detail:

- the `DirectoryTree` is rooted at `/` even when editing an existing path or when opened from the project directory
- this is intentional for now because using a non-root path caused broken / non-navigable tree behavior

Relevant file:

- `src/aicage/runtime/menu/textual/screens/share_editor_screen.py`

## Current styling direction

- Overview and subviews use a shared boxed-shell look.
- The app header is constrained inside the shell with `.app_header`.
- The shell is left-aligned instead of centered.
- Bind Mounts and Docker are stacked vertically in the overview, with Docker below Bind Mounts.
- The compact `+` button next to `Bind Mounts` uses stronger contrast so it reads as clickable.
- The overview shell width is computed at runtime from content and capped to the current viewport width so the
  `Cancel` / `OK` buttons stay visible.
- The bind-mount editor popup is tighter vertically than the earlier PoC and fits split-terminal layouts better.
- The Textual command palette is disabled for this UI.
- The top app header now formats `aicage` more strongly than `container config`.
- The overview header context is currently:
  - `Agent: ...`
  - `Project: ...`
- The old `Choose a section...` hint line has been removed.
- Textual inline `Screen` borders are now disabled in app CSS.
  - this was the actual source of the persistent blank row above and below the inline menu
  - it was not caused by the temporary `exit note` workaround or by overview shell spacing alone
- `OverviewApp.INLINE_PADDING` is set to `0`.
  - this removes Textual's built-in extra newline above inline rendering

Important inline-mode conclusion from this session:

- `inline_no_clear=True` was the real reason the old "exit note" workaround existed
- Textual inline exit behavior is:
  - with `inline_no_clear=True` and no explicit exit renderable, Textual prints the final compositor into the shell
  - this leaves behind frame garbage / stale menu rows
- The current fix is:
  - run with `inline=True`
  - do not use `inline_no_clear=True`
  - exit directly
  - remove the fake exit-note render path entirely

Main style file:

- `config/textual/overview/app.tcss`

## Recent commits

Most relevant recent commits, newest first:

- `55fcc43` Remove Textual inline screen border
- `1fddd9d` Improve empty Textual extensions screen
- `3a9368e` Clear initial textual host access highlights
- `9f8911b` Disable textual command palette
- `3fe75c5` Add textual menu coverage for edge branches
- `1bebdc1` Remove dead textual extensions summary parameter
- `409cce2` Polish textual bind mount editor
- `30a4ba6` Improve textual extension bind mount rows
- `076a692` Simplify textual overview extensions summary
- `9e8fed5` Unify textual bind mount display formatting
- `7f40238` Improve bind mount editor popup
- `dcd81a1` Refactor textual overview structure
- `e25816c` Restructure textual menu package
- `1245244` Edit custom shares from textual overview
- `45650cb` Update task 37 handoff docs

## Current verification state

Latest full checks that were green:

- `pytest --cov=src --cov-report=term-missing`
- `./scripts/lint.sh`

Latest directly re-run checks during the final polish pass:

- `./scripts/lint.sh`
  - green in the project `.venv`
- focused Textual test files rerun repeatedly while polishing
  - `tests/aicage/runtime/menu/textual/test__app.py`
  - `tests/aicage/runtime/menu/textual/services/test_summary.py`
  - `tests/aicage/runtime/menu/textual/services/test__share_support.py`
  - `tests/aicage/runtime/menu/textual/services/test_host_access.py`
  - `tests/aicage/runtime/menu/textual/screens/test_extensions_screen.py`
  - `tests/aicage/runtime/menu/textual/screens/test_host_access_confirm_screen.py`
  - `tests/aicage/runtime/menu/textual/screens/test_share_editor_screen.py`
  - `tests/aicage/runtime/menu/textual/overview/test_view.py`
  - `tests/aicage/runtime/menu/textual/test__mount_display.py`

Most recent concrete re-run set during this session:

- `tests/aicage/runtime/menu/textual/test__app.py`
- `tests/aicage/runtime/menu/textual/test_entry.py`
- `tests/aicage/runtime/menu/textual/overview/test_view.py`
- `tests/aicage/runtime/menu/textual/screens/test_extensions_screen.py`
- `tests/aicage/runtime/menu/textual/screens/test_host_access_confirm_screen.py`
- `./scripts/lint.sh`

Older full-run reference from the earlier handoff:

- `677 passed, 40 skipped`
- `TOTAL 94%`
- lint green

## Open design / likely next steps

1. Continue the structural cleanup of the Textual package.
   - likely candidates are more extraction from `overview/view.py`, `host_access_confirm_screen.py`, and
     `services/_share_support.py`
   - keep respecting the repo visibility rules and private-module boundaries
2. Revisit wording around extension-provided bind mounts.
   - `Extension <id>` is functional but not polished
   - the central formatting now makes this easier to change in one place
3. Decide whether the blank padded prefix column for normal custom bind mounts is the final UX.
   - technically it keeps the list aligned
   - visually it introduces rows like `"   : /tmp/data"`
   - this may or may not be the desired final look
4. Revisit the `DirectoryTree` helper if desired.
   - current solution is intentionally simple: always root at `/`
   - do not assume non-root `DirectoryTree(path)` is workable without verifying behavior first
5. Continue visual polish of the overview layout and popup screens.
   - spacing
   - truncation of long bind-mount rows
   - whether more inspection affordances are needed

## Abandoned experiments / pitfalls

- replacing `SelectionList` with a custom rendered widget for content-driven width
- replacing bind-mount and Docker toggles with `DataTable`
- trying to root `DirectoryTree` at a non-root existing path and expecting it to stay navigable

Reason:

- the current direction is to keep standard Textual widgets where possible and layer small behavior improvements on top
