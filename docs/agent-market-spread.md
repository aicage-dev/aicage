# Agent market-spread assessment

Date: 2026-09-04

This is a qualitative refresh of the original placement rationale. It estimates developer attention and likely
familiarity, not installed-user counts, quality, security, or suitability for a particular workload. Those cannot be
inferred reliably from public data.

## Method

The assessment combines four deliberately rough signals:

- public community footprint, especially the relevant source repository's GitHub visibility and activity;
- reach of the sponsoring ecosystem and distribution channels;
- presence in current terminal-coding-agent discussions and integrations; and
- whether the product is a broadly applicable coding CLI rather than a specialist or early-stage offering.

GitHub stars are only a directional community signal: they can reflect age, launch attention, and non-users. They are
not used as a score or as a ranking. The linked repositories and vendor pages are the evidence snapshot for this review.

Placement means what a new aicage user is most likely to expect to find ready to use:

- **Built-in**: broad, durable market visibility or a major-platform default.
- **Custom sample**: relevant, but narrower, newer, more specialised, or less proven as a durable default.

## Current built-ins

| Agent | Spread assessment | Recommendation | Rationale |
| --- | --- | --- | --- |
| Claude Code | Very broad | Keep built-in | Leading general-purpose terminal agent. |
| Codex CLI | Very broad | Keep built-in | Leading general-purpose terminal agent. |
| GitHub Copilot CLI | Very broad | Keep built-in | GitHub distribution makes it an expected default. |
| Gemini CLI | Very broad | Keep built-in | Broad Google-backed open-source community. |
| OpenCode | Very broad | Keep built-in | Leading independent open-source community. |
| Qwen Code | Broad | Keep built-in | Strong global and Chinese ecosystem visibility. |
| Factory CLI (`droid` directory) | Broad | Keep built-in | High developer-agent visibility. |
| Antigravity CLI | Broad, recent | Keep built-in | High launch visibility; reassess after more adoption history. |
| Goose | Established | Keep built-in | Active provider-neutral open-source agent. |
| Crush | Established | Keep built-in | Strong terminal-developer community. |

## Current custom samples

| Agent | Spread assessment | Recommendation | Rationale |
| --- | --- | --- | --- |
| Cline | Very broad | **Move to built-in** | Large open-source and editor-community visibility. |
| Aider | Broad, established | Keep custom | Widely recognised, but below the built-in priority cut-off. |
| Kimi Code CLI | Broad, fast-growing | Keep custom; review next cycle | Global CLI use is less proven. |
| Hermes Agent | High launch attention | Keep custom; review next cycle | Default coding-CLI status not yet proven. |
| Kiro CLI | Significant, recent | Keep custom | Not yet durable across communities. |
| Amp CLI | Meaningful niche | Keep custom | Narrower than the broad-default group. |
| Auggie CLI | Meaningful niche | Keep custom | Concentrated among Augment users. |
| Mistral Vibe | Meaningful, recent | Keep custom | Early as a cross-provider terminal default. |
| Forge Code | Niche | Keep custom | Limited evidence of broad market spread. |

## Capacity-constrained placement changes

With the current number of built-in agents held constant, make one swap:

- Move `cline` to `aicage-image/agents`.
- Move `crush` to `aicage-custom-samples/agents`.

Cline has broader current mindshare and is more likely to be expected by a new user. Crush remains a good sample, but
its audience is more concentrated in the terminal and Charmbracelet community.

Keep `aider`, `kimi`, and `hermes` as samples. Aider is established, but should not receive a scarce built-in slot ahead
of the current set. Kimi and Hermes are the most plausible subsequent promotions, although the current evidence is more
about fresh attention than durable, broadly distributed CLI use.

If the built-in set must shrink further, move `agy` (Antigravity CLI) to custom next. Its launch visibility is high, but
it has the least proven durable adoption among the current built-ins.

## Review cadence

Repeat this assessment every six months, or after a major agent launch. Revisit a placement when at least two signals
change materially: community activity, cross-tool integrations, vendor/distribution reach, or recurring developer usage
outside the agent's home ecosystem.

## Evidence snapshot

- [Claude Code](https://github.com/anthropics/claude-code)
- [Codex CLI](https://github.com/openai/codex)
- [GitHub Copilot CLI](https://github.com/features/copilot/cli)
- [Gemini CLI](https://github.com/google-gemini/gemini-cli)
- [OpenCode](https://github.com/anomalyco/opencode)
- [Qwen Code](https://github.com/QwenLM/qwen-code)
- [Factory CLI](https://factory.ai/product/cli)
- [Antigravity CLI](https://antigravity.google/docs/cli-overview)
- [Goose](https://github.com/aaif-goose/goose)
- [Crush](https://github.com/charmbracelet/crush)
- [Cline](https://github.com/cline/cline)
- [Aider](https://github.com/Aider-AI/aider)
- [Kimi Code CLI](https://www.kimi-cli.com/)
- [Hermes Agent](https://github.com/NousResearch/hermes-agent)
- [Kiro CLI](https://kiro.dev/cli/)
- [Amp CLI](https://ampcode.com/)
- [Auggie CLI](https://docs.augmentcode.com/cli)
- [Mistral Vibe](https://mistral.ai/products/vibe)
- [Forge Code](https://forgecode.dev/)
