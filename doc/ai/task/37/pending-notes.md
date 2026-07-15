# Pending Notes

Task 37 is functionally close to done.

The remaining work is mostly small polish and selective cleanup, not major behavior changes.

## Likely remaining tweaks

- wording polish:
  - decide whether `Extension <id>` is the final user-facing prefix for extension bind mounts
  - consider whether confirmation-popup helper text needs any final shortening
- bind-mount list formatting:
  - decide whether plain custom bind mounts should keep the blank padded prefix column
  - long single-line bind-mount rows still truncate in narrow shells
- `DirectoryTree` helper:
  - currently always rooted at `/`
  - keep this unless non-root behavior is re-verified as stable
- empty extensions screen:
  - verify the real user experience of `Copy Command` in the target terminals
  - current implementation prefers OS clipboard helpers and only falls back to Textual OSC 52
  - if users still report clipboard problems, prefer a narrower UX fix over more clipboard complexity
- Textual package cleanup:
  - `overview/view.py`
  - `screens/host_access_confirm_screen.py`
  - `services/_share_support.py`

## Things intentionally left as-is

- Relative custom bind-mount paths still resolve against the project path.
  - this is existing shared behavior, not a Textual-only quirk
  - obvious user mistakes become visible immediately in the overview
- Extension bind mounts are still persisted per extension, not per individual mount path.
  - the UI now shows one row per resolved mount path
  - toggling any row from the same extension toggles the whole extension group
- The Textual command palette is disabled for this UI.
  - the default palette exposed unusable or misleading actions for this flow
- The host-access confirmation popup is narrower than other sub-screens.
  - this is intentional
  - it should stay independent of the generic `.screen_shell` width unless multiple sub-screens need the same change
- The overview no longer uses an "exit note" workaround.
  - this was removed after tracing Textual inline exit behavior
  - current direction is to use normal `inline=True` exit instead of `inline_no_clear=True`
- The blank row above/below the inline menu was traced to Textual's default inline `Screen` border.
  - current local override:
    - `Screen { border: none; }`
  - this should not be "cleaned up" as dead CSS without re-checking the visual behavior

## Last known good direction

- Keep the current overview structure.
- Accept that overview and sub-screens use different widths.
- Prefer small local styling adjustments over broader widget/layout redesigns.
- For Textual internals, inspect the local checkout at `../../Textualize/textual/` first.
