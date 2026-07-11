# Q&A

## Questions

1. Do you want the first implementation to use Textual immediately, or do you want a first internal refactor plus a
   simple terminal UI without adding that dependency yet?
2. For the first increment, is it acceptable to support editing only these categories: base, extensions, shares, and
   “extras” (--docker, git/ssh/gnupg/gitroot mounts, persisted docker args), while leaving agent selection fixed from
   CLI?
3. On consecutive starts, should the initial overview be shown every time by default, or only when a new flag is passed
   and otherwise keep today’s “continue directly” behavior for now?
4. For non-interactive usage, should CLI arguments still fully override the UI path when provided, or should they only
   prefill values and still show the overview unless --yes is used?

## Answers

1. Refactor first
2. Yes
3. Show every time - that's the reson why it shuold be reasonably slim in height.
4. Prefill, `--yes` prevents showing the new UI, we may tweak that to show either config menu or none.
