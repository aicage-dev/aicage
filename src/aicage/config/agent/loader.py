from pathlib import Path

from aicage.config.agent._custom_loader import load_custom_agents
from aicage.config.agent._loader_shared import load_agents_from_directory
from aicage.config.agent.models import AgentMetadata
from aicage.config.base.models import BaseMetadata
from aicage.config.errors import ConfigError
from aicage.config.resources import find_packaged_path

_AGENT_DEFINITION_FILES: tuple[str, str] = ("agent.yaml", "agent.yml")


def load_agents(bases: dict[str, BaseMetadata]) -> dict[str, AgentMetadata]:
    builtin_agents = _load_builtin_agents(bases)
    custom_agents = load_custom_agents(bases)
    merged_agents = dict(builtin_agents)
    merged_agents.update(custom_agents)
    return merged_agents


def _load_builtin_agents(bases: dict[str, BaseMetadata]) -> dict[str, AgentMetadata]:
    agents_dir = _builtin_agents_dir()
    if not agents_dir.is_dir():
        raise ConfigError(f"Built-in agent directory '{agents_dir}' is missing.")
    return load_agents_from_directory(
        agents_dir=agents_dir,
        bases=bases,
        definition_files=_AGENT_DEFINITION_FILES,
        agent_label="Agent",
    )


def _builtin_agents_dir() -> Path:
    dockerfile = find_packaged_path("agent-build/Dockerfile")
    return dockerfile.parent / "agents"
