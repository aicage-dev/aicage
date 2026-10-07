# ACP support for configured agents

<!-- pyml disable line-length -->
| Agent                                | Source         | ACP support                | ACP command or adapter                                                        |
|--------------------------------------|----------------|----------------------------|-------------------------------------------------------------------------------|
| Aider                                | Custom samples | No native ACP              | No recommended active adapter                                                 |
| Amp CLI                              | Custom samples | Third-party adapter        | [`amp-acp`](https://github.com/tao12345666333/amp-acp)                        |
| Auggie CLI                           | Custom samples | Native                     | `auggie --acp`                                                                |
| Cline CLI                            | Custom samples | Native                     | `cline --acp`                                                                 |
| Crush                                | Custom samples | No native ACP              | No recommended active adapter                                                 |
| [Forge Code](https://forgecode.dev/) | Custom samples | No verified ACP agent mode | N/A                                                                           |
| Kimi Code CLI                        | Custom samples | Native                     | `kimi acp`                                                                    |
| Kiro CLI                             | Custom samples | Native                     | `kiro acp`                                                                    |
| Mistral Vibe                         | Custom samples | Native adapter             | [`vibe-acp`](https://docs.mistral.ai/vibe/code/use-vibe-in-other-ides)        |
| Antigravity CLI                      | Image          | No native ACP              | No recommended active adapter                                                 |
| Claude Code                          | Image          | Wrapper                    | [`claude-agent-acp`](https://github.com/agentclientprotocol/claude-agent-acp) |
| Codex CLI                            | Image          | Wrapper                    | [`codex-acp`](https://github.com/agentclientprotocol/codex-acp)               |
| GitHub Copilot CLI                   | Image          | Native                     | `copilot --acp --stdio`                                                       |
| Factory CLI                          | Image          | Native                     | `droid exec --output-format acp`                                              |
| Gemini CLI                           | Image          | Experimental native        | `gemini --experimental-acp`                                                   |
| Goose CLI                            | Image          | Native                     | `goose acp`                                                                   |
| OpenCode                             | Image          | Native                     | `opencode acp`                                                                |
| Qwen Code                            | Image          | Native                     | `qwen --acp`                                                                  |
<!-- pyml enable line-length -->

Forge Code is a standalone, multi-provider coding CLI with its own local agents (`forge`, `muse`, and `sage`). It is
not an ACP framework or bridge, and its documentation does not describe an ACP agent mode.
