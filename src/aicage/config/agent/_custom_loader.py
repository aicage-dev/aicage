from aicage.config.agent._loader_shared import load_agents_from_directory
from aicage.config.agent.models import AgentMetadata
from aicage.config.base.models import BaseMetadata
from aicage.paths import CUSTOM_AGENT_DEFINITION_FILES, CUSTOM_AGENTS_DIR


def load_custom_agents(
    bases: dict[str, BaseMetadata],
) -> dict[str, AgentMetadata]:
    agents_dir = CUSTOM_AGENTS_DIR
    if not agents_dir.is_dir():
        return {}
    return load_agents_from_directory(
        agents_dir=agents_dir,
        bases=bases,
        definition_files=CUSTOM_AGENT_DEFINITION_FILES,
        agent_label="Custom agent",
    )
