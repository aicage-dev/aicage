# ACP support for aicage agents

Agents configured under `../aicage-image/agents/*` and `../aicage-custom-samples/*` with confirmed ACP support.

## ../aicage-image/agents

- **Hermes Agent**
  - Status: native
  - Call: `hermes acp`, `hermes-acp`, or `python -m acp_adapter`
  - Notes: requires ACP extra; logs to stderr so stdout stays on the JSON-RPC stream.

- **OpenCode**
  - Status: native
  - Call: `opencode acp`
  - Notes: stdio JSON-RPC over stdin/stdout; one ACP client per process.

- **Codex CLI**
  - Status: wrapper
  - Call: `codex-acp`
  - Notes: not native; Zed's `@zed-industries/codex-acp` wrapper exposes Codex over ACP stdio.

- **Claude Code**
  - Status: wrapper
  - Call: `claude-code-acp`
  - Notes: not native; Zed's `@zed-industries/claude-code-acp` wrapper exposes Claude Code over ACP stdio.

- **Copilot CLI**
  - Status: native
  - Call: `copilot --acp --stdio`
  - Notes: also supports TCP mode via `--acp --port <port>`.

- **Gemini CLI**
  - Status: experimental/native
  - Call: `gemini --experimental-acp`
  - Notes: official `--experimental-acp` flag in CLI options.

- **Goose**
  - Status: native
  - Call: `goose acp`
  - Notes: client/server over stdio; MCP servers from the client are forwarded.

- **Qwen Code**
  - Status: native
  - Call: `qwen --acp`
  - Notes: recognized in ACP bridge test matrices as `--acp` stdio agent.

## ../aicage-custom-samples/agents

- **Hermes Agent**
  - Status: native
  - Call: `hermes acp`
  - Notes: same as image variant.

- **OpenCode**
  - Status: native
  - Call: `opencode acp`
  - Notes: same as image variant.

- **Cline**
  - Status: native
  - Call: `cline --acp`
  - Notes: full ACP lifecycle documented; JetBrains preset in official docs.

- **Kimi CLI**
  - Status: native
  - Call: `kimi acp`
  - Notes: JSON-RPC over stdin/stdout; multi-session server.

- **Kiro CLI**
  - Status: native
  - Call: `kiro acp`
  - Notes: AWS-backed ACP harness; stdio local mode and WebSocket remote mode.

- **Auggie**
  - Status: native
  - Call: `auggie --acp`
  - Notes: first-class ACP agent per Augment docs.

- **Mistral Vibe**
  - Status: native adapter
  - Call: `vibe-acp`
  - Notes: ships with `mistral-vibe` repo as the ACP-facing entrypoint.

- **Amp CLI**
  - Status: third-party adapter
  - Call: `amp-acp`
  - Notes: community adapter bridges Amp CLI to ACP; Amp itself has no native ACP flag.

- **Forge**
  - Status: framework/agent harness
  - Call: `forge`
  - Notes: Forge implements ACP and orchestrates other agents through it; not a simple agent CLI.

- **Aider**
  - Status: unclear
  - Call: `aider`
  - Notes: no native ACP flag or official docs found; OmniRoute lists it as an ACP stdio agent but the claim appears to be adapter-side behavior.

- **Antigravity CLI / agy**
  - Status: unclear
  - Call: `agy`
  - Notes: no native ACP support at launch; community `antigravity-acp` adapters exist.

## Not supported / no ACP evidence found

- `../aicage-image/agents/crush`
- `../aicage-image/agents/droid`
- `../aicage-image/agents/gemini` (no separate `gemini` agent in custom samples)
