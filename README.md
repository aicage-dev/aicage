# aicage

Run your favorite AI coding agents comfortably in Docker.

## Why use `aicage`?

Agents need deep access (read code, run shells, install deps).
Their built-in safety checks are naturally limited.

Running agents in containers gives a hard boundary - while the experience stays the same.
See [Why cage agents?](#why-cage-agents) for the full rationale.

## Quickstart (first run)

- Prerequisites:
  - Docker
  - Python 3.10+ and `pipx`
- Install:
  
  ```bash
  pipx install aicage
  ```
  
- Navigate to your project directory.
- Fastest start (accept defaults, no setup prompts):

  ```bash
  aicage --yes <agent>
  ```

  This is the quickest way to get started the first time.

- Built-in agent examples:

  ```bash
  aicage --yes claude
  aicage --yes codex
  aicage --yes copilot
  aicage --yes crush
  aicage --yes droid
  aicage --yes gemini
  aicage --yes goose
  aicage --yes opencode
  aicage --yes qwen
  ```

## Full setup (optional)

If you want to review and re-run full interactive setup:

1. Print the current project config:

   ```bash
   aicage --config info
   ```

2. If needed, remove saved config for the project or one agent:

   ```bash
   aicage --config remove
   aicage --config remove <agent>
   ```

3. Run again without `--yes` to go through all prompts:

   ```bash
   aicage <agent>
   ```

4. Screenshot placeholder: full interactive setup flow.

## Full documentation

The complete user documentation lives in the wiki:
[aicage.wiki](https://github.com/aicage/aicage/wiki)

## Common scenarios

- Pass arguments to the agent:
  - `aicage <agent> resume <session-id>`
- Share additional host folders:
  - `aicage --share ~/.m2 <agent>`
  - `aicage --share /path/to/data:ro <agent>`
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

## Base images

The first run asks which base image to use; pick Ubuntu or whatever matches your Linux distro.  
All base images have the same stack of tools installed.

## Agents

| CLI      | Agent              | Homepage                                                                           |
|----------|--------------------|------------------------------------------------------------------------------------|
| claude   | Claude Code        | [https://claude.com/product/claude-code](https://claude.com/product/claude-code)   |
| codex    | Codex CLI          | [https://developers.openai.com/codex/cli](https://developers.openai.com/codex/cli) |
| copilot  | GitHub Copilot CLI | [https://github.com/features/copilot/cli](https://github.com/features/copilot/cli) |
| crush    | Crush              | [https://github.com/charmbracelet/crush](https://github.com/charmbracelet/crush)   |
| droid    | Factory CLI        | [https://factory.ai/product/cli](https://factory.ai/product/cli)                   |
| gemini   | Gemini CLI         | [https://geminicli.com](https://geminicli.com)                                     |
| goose    | Goose CLI          | [https://block.github.io/goose](https://block.github.io/goose)                     |
| opencode | OpenCode           | [https://opencode.ai](https://opencode.ai)                                         |
| qwen     | Qwen Code          | [https://qwenlm.github.io/qwen-code-docs](https://qwenlm.github.io/qwen-code-docs) |

Your existing CLI config for each agent is mounted inside the container so you can keep using your
preferences and credentials.

## Customization

You can customize images at three levels: extensions, agents, and base images.

- Extensions: [Customization-Extensions](https://github.com/aicage/aicage/wiki/Customization-Extensions)
- Custom agents: [Customization-Agents](https://github.com/aicage/aicage/wiki/Customization-Agents)
- Custom base images: [Customization-Base-Images](https://github.com/aicage/aicage/wiki/Customization-Base-Images)

Image updates are handled automatically; see [Updates](https://github.com/aicage/aicage/wiki/Updates).

## aicage options

- `--dry-run` prints the composed `docker run` command without executing it.
- `-y`, `--yes` applies default answers for all prompts and suppresses prompt output.
- `--docker` mounts `/run/docker.sock` into the container to enable Docker-in-Docker workflows.
- `--share <path>` mounts a host path into the container at the same path. Repeatable; add `:ro` for read-only.
- `--config info` prints the project config path and its contents.
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
