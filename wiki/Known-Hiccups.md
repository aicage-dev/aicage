# Known hiccups

These are known first-use issues that can look like hard failures but are usually one-time setup friction.

## Authentication methods that require host browser automation

`aicage` runs agents inside a container. Authentication methods that try to open a browser directly from the
container often do not work on the host machine.

Use authentication options that give you a URL and code to open manually on the host. In Codex CLI, choose
`Sign in with Device Code` instead of browser-driven login from inside the container.

This is typically a one-time setup per agent.

## Claude first run with empty `~/.claude.json`

If no Claude config exists on the host yet, `~/.claude.json` may be created as an empty file on first run. Claude
then reports a JSON parse error.

Fix:

1. Choose `Reset with default configuration` in Claude's prompt.
2. Continue setup.

After this reset, future runs should start normally.

## Windows host + Linux container line-ending diffs

When using a Linux runtime (Docker/WSL) on a Windows host, Git can show unexpected diffs if line-ending conversion is
not configured on the host.

Set this on the Windows host:

```bash
git config --global core.autocrlf true
```

This prevents many CRLF/LF mismatch diffs in shared workspaces.
