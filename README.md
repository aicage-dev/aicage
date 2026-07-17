# aicage

Run your favorite AI coding agents comfortably in Docker.

## Why use `aicage`?

Agents need deep access (read code, run shells, install deps).
Their built-in safety checks are naturally limited.

Running agents in containers gives a hard boundary - while the experience stays the same.
See [Why cage agents?](#why-cage-agents) for the full rationale.

## First-time quick start

- Prerequisites:
  - Docker
  - Python 3.10+ and `pipx`
- Install:
  
  ```bash
  pipx install aicage
  ```
  
- Navigate to your project directory and run:

  ```bash
  aicage <agent>
  ```

This opens the default Textual configuration UI where you can review and adjust the setup before starting.

- Built-in agent examples:

  ```bash
  aicage agy
  aicage claude
  aicage codex
  aicage copilot
  aicage crush
  aicage droid
  aicage gemini
  aicage goose
  aicage opencode
  aicage qwen
  ```

If you want the fastest no-menu first run, use:

```bash
aicage --menu none <agent>
```

`--menu none` accepts suggested defaults and skips interactive menus.

## Menu modes

- `aicage <agent>` uses the default Textual configuration UI.
- `aicage --menu simple <agent>` uses the classic line-based prompt menu.
- `aicage --menu none <agent>` skips menus and uses defaults.

Run `aicage <agent>` again whenever you want to review or change the saved config for that agent in the current
project.

Use `--config remove` only when you want to reset the saved config completely.

1. Show project config path and contents:

   ```bash
   aicage --config info
   ```

2. Remove config if needed:

   ```bash
   aicage --config remove
   aicage --config remove <agent>
   ```

## Full documentation

The complete user documentation lives in the wiki:
[aicage.wiki](https://github.com/aicage/aicage/wiki)

## Common scenarios

- Pass arguments to the agent:
  - `aicage <agent> resume <session-id>`
- Share additional host folders:
  - `aicage --share ~/.m2 <agent>`
  - `aicage --share /path/to/data:ro <agent>`
  - Extensions can also define extra shares (host mounts).
- Let the agent use Docker:
  - `aicage --docker <agent>`
- Set environment variables:
  - `aicage -e FOO=bar -- <agent>`
- Use proxies:
  - `aicage` forwards `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, and `NO_PROXY`.
  - See [CLI options](https://github.com/aicage/aicage/wiki/CLI-Options).
- Use host networking or custom networks:
  - See [Host networking](https://github.com/aicage/aicage/wiki/Host-Networking).
- On Windows with a Linux container/WSL workspace:
  - set `git config --global core.autocrlf true` on the Windows host to avoid line-ending diffs.
- Run into first-use setup issues:
  - See [Known hiccups](https://github.com/aicage/aicage/wiki/Known-Hiccups).
- Add custom tools/agents/base images:
  - [Extensions](https://github.com/aicage/aicage/wiki/Customization-Extensions)
  - [Custom agents](https://github.com/aicage/aicage/wiki/Customization-Agents)
  - [Custom base images](https://github.com/aicage/aicage/wiki/Customization-Base-Images)

## Built-in agents

<!-- pyml disable line-length -->
| CLI      | Agent              | Homepage                                                                           |
|----------|--------------------|------------------------------------------------------------------------------------|
| agy      | Antigravity CLI    | [https://antigravity.google/docs/cli-overview](https://antigravity.google/docs/cli-overview) |
| claude   | Claude Code        | [https://claude.com/product/claude-code](https://claude.com/product/claude-code)   |
| codex    | Codex CLI          | [https://developers.openai.com/codex/cli](https://developers.openai.com/codex/cli) |
| copilot  | GitHub Copilot CLI | [https://github.com/features/copilot/cli](https://github.com/features/copilot/cli) |
| crush    | Crush              | [https://github.com/charmbracelet/crush](https://github.com/charmbracelet/crush)   |
| droid    | Factory CLI        | [https://factory.ai/product/cli](https://factory.ai/product/cli)                   |
| gemini   | Gemini CLI         | [https://geminicli.com](https://geminicli.com)                                     |
| goose    | Goose CLI          | [https://goose-docs.ai](https://goose-docs.ai)                                     |
| opencode | OpenCode           | [https://opencode.ai](https://opencode.ai)                                         |
| qwen     | Qwen Code          | [https://qwenlm.github.io/qwen-code-docs](https://qwenlm.github.io/qwen-code-docs) |
<!-- pyml enable line-length -->

Your existing CLI config for each agent is mounted inside the container so you can keep using your
preferences and credentials.

## Customization

`aicage` lets you customize images at three levels: extensions, agents, and base images. The sample repo is a fast
way to see working examples and copy a template.

Quick start:

```bash
git clone https://github.com/aicage/aicage-custom-samples.git $HOME/.aicage-custom
```

Then run any agent:

```bash
aicage <agent>
```

These are only samples. Use them to learn the structure, then replace or edit them with your own definitions.
`aicage` detects whatever you place under `~/.aicage-custom` and offers it during selection.
Extensions can install tools and request additional host mounts.

After adding or changing custom definitions, restart `aicage`.

If your project is already configured for an agent, rerun `aicage <agent>` to review or change that saved config.
Use `aicage --config remove` only to reset the whole project config, or `aicage --config remove <agent>` to reset a
single agent entry. Use `aicage --config` to inspect the current config.

- Extensions: [Customization-Extensions](https://github.com/aicage/aicage/wiki/Customization-Extensions)
- Custom agents: [Customization-Agents](https://github.com/aicage/aicage/wiki/Customization-Agents)
- Custom base images: [Customization-Base-Images](https://github.com/aicage/aicage/wiki/Customization-Base-Images)

Image updates are handled automatically; see [Updates](https://github.com/aicage/aicage/wiki/Updates).

## aicage options

- `--dry-run` prints the composed `docker run` command without executing it.
- `--menu textual|simple|none` selects the Textual menu, the simple line-based menu, or no menu.
- `--docker` mounts `/run/docker.sock` into the container to enable Docker-in-Docker workflows.
- `--share <path>` mounts a host path into the container at the same path. Repeatable; add `:ro` for read-only.
- Extensions can also request grouped host mounts during setup.
- `--config` prints the project config path and its contents.
- `--config remove [<agent>]` removes the full project config or only one agent entry.

Configuration file formats are documented in [CONFIG.md](CONFIG.md). Extension authoring is documented in
[doc/extensions.md](doc/extensions.md).

## Why cage agents?

AI coding agents read your code, run shells, install packages, and edit files. That power is useful,
but granting it directly on the host expands your risk surface.

Where built-in safety is limited:

- Allow/deny lists only cover known patterns; unexpected commands or attack paths can slip through.
- Some agents work fully only after relaxing their own safety modes, broadening what they can touch.
- “Read-only project” features are software rules. Other projects and files still sit alongside them
  on the same host.

How aicage mitigates this:

- Containers create a hard boundary: the agent can access only what you explicitly mount. Day-to-day
  use stays familiar—just with the host kept out of reach.
