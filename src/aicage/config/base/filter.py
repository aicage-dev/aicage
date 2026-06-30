from aicage.config._base_exclude import is_base_excluded, normalize_exclude
from aicage.config.agent.models import AgentMetadata
from aicage.config.base.architecture import base_supports_host_architecture
from aicage.config.context import ConfigContext


def filter_bases(context: ConfigContext, agent_metadata: AgentMetadata) -> set[str]:
    base_exclude = normalize_exclude(agent_metadata.base_exclude)
    base_distro_exclude = normalize_exclude(agent_metadata.base_distro_exclude)
    filtered: set[str] = set()
    for base_name, base_metadata in context.bases.items():
        if is_base_excluded(
            base_name,
            base_metadata.base_image_distro,
            base_exclude,
            base_distro_exclude,
        ):
            continue
        if not base_supports_host_architecture(base_metadata.architectures):
            continue
        filtered.add(base_name)
    return filtered
