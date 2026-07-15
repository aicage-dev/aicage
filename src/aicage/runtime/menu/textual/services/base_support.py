from aicage.config.agent.models import AgentMetadata
from aicage.config.base.filter import filter_bases
from aicage.config.base.models import BaseMetadata
from aicage.config.context import ConfigContext
from aicage.config.run_config_draft import RunConfigDraft
from aicage.registry.errors import RegistryError
from aicage.runtime.menu.default_base import resolve_default_base


def _base_options_for_draft(draft: RunConfigDraft, context: ConfigContext) -> list[str]:
    agent_metadata = _require_agent_metadata(draft.agent, context)
    filtered = _filtered_bases(context, agent_metadata)
    if not filtered:
        raise RegistryError(f"Agent '{draft.agent}' does not define any valid bases.")
    return sorted(filtered)


def base_metadata_for_draft(
    draft: RunConfigDraft, context: ConfigContext
) -> dict[str, BaseMetadata]:
    agent_metadata = _require_agent_metadata(draft.agent, context)
    filtered = _filtered_bases(context, agent_metadata)
    if not filtered:
        raise RegistryError(f"Agent '{draft.agent}' does not define any valid bases.")
    return {base: context.bases[base] for base in sorted(filtered)}


def ensure_base_default(draft: RunConfigDraft, context: ConfigContext) -> None:
    if draft.agent_cfg.base:
        return
    draft.agent_cfg.base = resolve_default_base(_base_options_for_draft(draft, context))


def _require_agent_metadata(agent: str, context: ConfigContext) -> AgentMetadata:
    agent_metadata = context.agents.get(agent)
    if not agent_metadata:
        raise RegistryError(f"Agent '{agent}' is missing from config context.")
    return agent_metadata


def _filtered_bases(context: ConfigContext, agent_metadata: AgentMetadata) -> set[str]:
    return filter_bases(context, agent_metadata)
