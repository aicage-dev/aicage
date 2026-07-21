from pathlib import Path

from aicage.config._yaml_loader import load_yaml
from aicage.config.agent._metadata import build_agent_metadata
from aicage.config.agent._validation import ensure_required_files
from aicage.config.agent.models import AgentMetadata
from aicage.config.base.models import BaseMetadata
from aicage.config.errors import ConfigError


def load_agents_from_directory(
    agents_dir: Path,
    bases: dict[str, BaseMetadata],
    definition_files: tuple[str, ...],
    agent_label: str,
) -> dict[str, AgentMetadata]:
    agents: dict[str, AgentMetadata] = {}
    for entry in sorted(agents_dir.iterdir()):
        if not entry.is_dir():
            continue
        agent_name = entry.name
        agent_path = _find_agent_definition(entry, definition_files, agent_label)
        agent_mapping = load_yaml(agent_path)
        ensure_required_files(agent_name, entry)
        agents[agent_name] = build_agent_metadata(
            agent_name=agent_name,
            agent_mapping=agent_mapping,
            bases=bases,
            definition_dir=entry,
        )
    return agents


def _find_agent_definition(
    agent_dir: Path, definition_files: tuple[str, ...], agent_label: str
) -> Path:
    for filename in definition_files:
        candidate = agent_dir / filename
        if candidate.is_file():
            return candidate
    expected = ", ".join(definition_files)
    raise ConfigError(f"{agent_label} '{agent_dir.name}' is missing {expected}.")
