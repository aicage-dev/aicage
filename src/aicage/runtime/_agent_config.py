import os
from dataclasses import dataclass
from pathlib import Path

from aicage.config.agent.models import AgentMetadata
from aicage.runtime._path_utils import ensure_path_exists, looks_like_file


@dataclass
class AgentConfig:
    agent_path: list[str]
    agent_config_host: list[Path]


def resolve_agent_config(agent_metadata: AgentMetadata) -> AgentConfig:
    agent_paths = agent_metadata.agent_path
    agent_config_hosts = [_ensure_agent_path(path) for path in agent_paths]
    return AgentConfig(agent_path=agent_paths, agent_config_host=agent_config_hosts)


def _ensure_agent_path(agent_path: str) -> Path:
    expanded = Path(os.path.expanduser(agent_path)).resolve()
    return ensure_path_exists(expanded, looks_like_file(agent_path))
