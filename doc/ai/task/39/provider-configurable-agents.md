# Provider configuration for configured agents

This complements [ACP support for configured agents](acp-capable-image-agents.md).

## Summary

<!-- pyml disable md013 -->
| Agent              | Source         | Other providers or models | OpenRouter                     | Notes                                                                                          |
|--------------------|----------------|---------------------------|--------------------------------|------------------------------------------------------------------------------------------------|
| Aider              | Custom samples | Yes                       | Direct                         | Native LiteLLM-based provider support; not an ACP agent.                                       |
| Antigravity CLI    | Custom samples | Not verified              | Not verified                   | Do not advertise without an upstream configuration reference.                                  |
| Cline CLI          | Custom samples | Yes                       | Direct                         | Cline supports OpenRouter and several other API providers.                                     |
| Crush              | Custom samples | Yes                       | Direct                         | Supports OpenRouter, Anthropic, OpenAI, Gemini, and others.                                    |
| Forge Code         | Custom samples | Yes                       | Verify before use              | It is described as multi-provider, but its current provider matrix needs an upstream check.    |
| Kimi Code CLI      | Custom samples | Yes                       | Via OpenAI-compatible provider | Supports OpenAI-compatible, Anthropic, Gemini, and Vertex providers.                           |
| Amp CLI            | Image          | No                        | No                             | Uses Amp's managed service.                                                                    |
| Auggie CLI         | Image          | No                        | No                             | Uses Augment's managed service.                                                                |
| Claude Code        | Image          | Limited                   | Yes (verified)                 | Add URL, model and API-key by ENV variables, see [claude env-vars].                            |
| Codex CLI          | Image          | Limited                   | Yes (verified)                 | Add [~/.codex/openrouter.config.toml][codex config.toml] and use `codex --profile openrouter`. |
| GitHub Copilot CLI | Image          | No                        | No                             | Model choice is limited to Copilot's offered models.                                           |
| Factory Droid      | Image          | BYOK exists               | Yes (verified)                 | Add provider and model in [~/.factory/settings.json][droid settings.json].                     |
| Goose              | Image          | Yes                       | Direct                         | Add provider, model and API-key by ENV variables, see [goose env-vars].                        |
| Kiro CLI           | Image          | No                        | No                             | AWS/Kiro service credentials and supported models apply.                                       |
| OpenCode           | Image          | Yes                       | Direct                         | Add provider and model in [~/.config/opencode/opencode.json][opencode.json].                   |
| Qwen Code          | Image          | Yes                       | Direct                         | Add URL, model and API-key by ENV variables, see [qwen env-vars].                              |
| Mistral Vibe       | Image          | Yes                       | Yes (verified)                 | Add provider and model in [~/.vibe/config.toml](agent-config/vibe/config.toml).                |
<!-- pyml enable md013 -->

“Direct” means the CLI has an OpenRouter integration or documents OpenRouter as an OpenAI-compatible provider.
“Gateway only” means the agent must be pointed at a compatible intermediary; it does not mean every OpenRouter model or
tool-calling behavior will work unchanged. “Verify” is intentional: do not represent a generic `base_url` setting or a
marketing BYOK claim as confirmed OpenRouter compatibility.

## Upstream references

- [Aider OpenRouter setup](https://aider.chat/docs/llms/openrouter.html)
- [Goose provider overview](https://block.github.io/goose/)
- [Kimi Code providers and models](https://www.kimi.com/code/docs/en/kimi-code-cli/configuration/providers)
- [OpenCode providers](https://docs.opencode.ai/docs/providers/)
- [Qwen Code model providers](https://github.com/QwenLM/qwen-code/blob/main/docs/users/configuration/model-providers.md)
- [Claude Code LLM gateway configuration](https://docs.anthropic.com/en/docs/claude-code/llm-gateway)
- [Codex configuration reference](https://developers.openai.com/codex/config-reference)

[claude env-vars]: agent-config/claude/env-vars
[codex config.toml]: agent-config/codex/openrouter.config.toml
[droid settings.json]: agent-config/droid/settings.json
[goose env-vars]: agent-config/goose/env-vars
[opencode.json]: agent-config/opencode/opencode.json
[qwen env-vars]: agent-config/qwen/env-vars
