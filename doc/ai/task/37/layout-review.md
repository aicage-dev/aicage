# Layout Review

Screenshot review scope:

- reviewed:
  - `doc/ai/task/37/screenshots/Screenshot_overview.png`
  - `doc/ai/task/37/screenshots/Screenshot_base.png`
  - `doc/ai/task/37/screenshots/Screenshot_extensions.png`
  - `doc/ai/task/37/screenshots/Screenshot_docker_args.png`
  - `doc/ai/task/37/screenshots/Screenshot_confirmation_popup.png`
- excluded:
  - `share_*_popup` screenshots

## Ranked issues

1. Normalize the overview vertical rhythm as a whole.
   The top `Base` / `Extensions` / `Docker Args` row feels much taller and more card-like than the denser list layout
   below it. The transition is abrupt.
2. Improve the `Bind Mounts` header row alignment.
   The `+` button works, but it still reads somewhat bolted onto the header instead of feeling naturally aligned with it.
3. Strengthen grouping for the overview `Docker` section.
   This is less a broken layout issue and more a hierarchy issue. The section reads more weakly than comparable grouped
   sections in the confirmation popup.
4. Watch long bind-mount rows in narrower shells.
   The current single-line `SelectionList` rows still truncate once the overview reaches the viewport cap.
5. Re-check the empty extensions screen visually after the latest copy-command work.
   The behavior is materially better, but the final visual balance was not deeply re-reviewed here.

## Recommended first fixes

If the goal is a safe polish pass with minimal layout churn, start with:

1. the overview lower-half grouping / hierarchy
2. the `Bind Mounts` header alignment

Things resolved during this session and no longer good targets for random CSS poking:

1. The persistent blank row above / below the inline menu.
   This was traced to Textual's default inline `Screen` border, not to overview shell margins.
2. The old inline exit garbage / stale frame issue.
   This was traced to `inline_no_clear=True`, not to the content of the old exit-note widget.
