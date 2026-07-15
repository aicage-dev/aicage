# Shares and Extras View

This note is now mostly historical context for the host-access part of Task 37.

The big redesign already happened in code. The remaining work is polish, wording, and continued structural cleanup.

## Implemented outcome

### Bind mounts

These should now be thought of as `Bind Mounts` in the Textual UI, not `Shares`.

Current behavior:

- Bind mounts are managed directly on the overview.
- Built-in git-support bind mounts appear first in one `SelectionList`.
- Extension-provided bind mounts for selected extensions are included in that same list.
- Each resolved extension bind mount now gets its own row.
- Rows from the same extension still toggle and persist as one extension-level group.
- Custom bind mounts appear after them in the same list.
- There is a compact `+` button to add one custom bind mount.
- Built-in git-support bind mounts still toggle directly in the list.
- Selecting an existing custom bind mount opens the editor popup prefilled with that value.
- The custom bind mount popup offers `Remove` for deletion instead of deleting immediately from overview interaction.
- Custom bind mounts support read-only mode through a checkbox.

### Current list formatting

Formatting is now centralized in:

- `src/aicage/runtime/menu/textual/_mount_display.py`

Current conventions:

- built-in and extension items display as `<prefix>: <path>`
- custom read-only items display as `Read-only: <path>`
- custom read-write items use a blank padded prefix column so rows line up with prefixed items

That means built-in and custom items are still separate in the actual state model, but their rendered view is now
shared.

This split currently seems justified:

- built-in items carry persistence and enablement state
- custom items are just user-entered mount strings
- the display layer is where harmonization now happens

### Bind mount editor

The editor is no longer the minimal early text-only PoC.

Current popup contents:

- title:
  - `Add Bind Mount` or `Edit Bind Mount`
- text input:
  - `Host path`
- checkbox:
  - `Read-only`
- filesystem helper:
  - `DirectoryTree`
- buttons:
  - `Cancel`
  - optional `Remove`
  - `OK`
- pressing `Enter` in the text input accepts

Important current decision:

- `DirectoryTree` is always rooted at `/`

Reason:

- using a non-root path for `DirectoryTree(...)` produced broken behavior where only the tail segment was visible and the
  tree was not usefully navigable
- the current simple behavior is acceptable as a helper for selecting a fresh path

### Docker socket / Docker Args split

`Docker socket` is no longer edited in the Docker arguments screen.

Current behavior:

- it lives in a separate `Docker` list on the overview
- it stays visually separate from file/path bind mounts
- it participates in the same final host-access confirmation flow as the git-support bind mounts

### Confirmation flow

The host-access confirmation popup is unified.

Current sections:

- `Docker support`
- `Git support`
- `Extension bind mounts`

Only newly enabled items are shown.

That includes extension-provided bind mounts:

- if an extension such as `gh` contributes a hidden bind mount
- and stored state did not already have it enabled
- the final confirmation popup shows it before saving
- the popup now clears initial per-list row highlight when focus starts on `OK`

### Docker arguments editor

The old extras screen is now effectively a Docker arguments editor.

Current state:

- multiline `TextArea`
- `Ctrl+Enter` accepts
- `Clear` clears the live editor state
- `Cancel` still discards changes

## Still-open ideas

### Bind mount wording

The old internal `share` naming still exists in code and CLI options, but user-facing Textual wording should keep moving
toward `Bind Mounts`.

Potential follow-up:

- revisit whether `Extension <id>` is the right user-facing prefix
- keep any future prefix changes centralized in `_mount_display.py`

### Prefix alignment

The current aligned list formatting is technically correct, but there is still a UX question:

- should ordinary custom paths really show as a blank prefix plus `:`
- or should alignment be achieved some other way

That is a design choice, not a structural blocker.

### Structural cleanup

The Textual package is cleaner than before, but still young and still settling.

Likely future refactor targets:

- `overview/view.py`
- `screens/host_access_confirm_screen.py`
- `services/_share_support.py`

The recent direction that seems to work:

- keep state models simple
- extract shared display helpers where useful
- avoid over-fragmenting files without a real reduction in complexity

## Summary

The original Shares / Extras redesign is done.

The remaining work is now:

- continued cleanup of Textual package structure
- wording polish
- list-row polish
- optional future improvement around the filesystem chooser
