# ACP support for configured agents

<!-- pyml disable line-length -->
| Agent                                | Source         | ACP support                | ACP command or adapter                                                        |
|--------------------------------------|----------------|----------------------------|-------------------------------------------------------------------------------|
| Aider                                | Custom samples | No native ACP              | No recommended active adapter                                                 |
| Antigravity CLI                      | Custom samples | No native ACP              | No recommended active adapter                                                 |
| Cline CLI                            | Custom samples | Native                     | `cline --acp`                                                                 |
| Crush                                | Custom samples | No native ACP              | No recommended active adapter                                                 |
| [Forge Code](https://forgecode.dev/) | Custom samples | No verified ACP agent mode | N/A                                                                           |
| Kimi Code CLI                        | Custom samples | Native                     | `kimi acp`                                                                    |
| Amp CLI                              | Image          | Third-party adapter        | [`amp-acp`](https://github.com/tao12345666333/amp-acp)                        |
| Auggie CLI                           | Image          | Native                     | `auggie --acp`                                                                |
| Claude Code                          | Image          | Wrapper                    | [`claude-agent-acp`](https://github.com/agentclientprotocol/claude-agent-acp) |
| Codex CLI                            | Image          | Wrapper                    | [`codex-acp`](https://github.com/agentclientprotocol/codex-acp)               |
| GitHub Copilot CLI                   | Image          | Native                     | `copilot --acp --stdio`                                                       |
| Factory CLI                          | Image          | Native                     | `droid exec --output-format acp`                                              |
| Goose CLI                            | Image          | Native                     | `goose acp`                                                                   |
| Kiro CLI                             | Image          | Native                     | `kiro acp`                                                                    |
| OpenCode                             | Image          | Native                     | `opencode acp`                                                                |
| Qwen Code                            | Image          | Native                     | `qwen --acp`                                                                  |
| Mistral Vibe                         | Image          | Native adapter             | [`vibe-acp`](https://docs.mistral.ai/vibe/code/use-vibe-in-other-ides)        |
<!-- pyml enable line-length -->

Forge Code is a standalone, multi-provider coding CLI with its own local agents (`forge`, `muse`, and `sage`). It is
not an ACP framework or bridge, and its documentation does not describe an ACP agent mode.
