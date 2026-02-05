import os
from dataclasses import dataclass
from pathlib import Path

from aicage.config.agent.models import AgentMetadata
from aicage.runtime._path_utils import ensure_path_exists


@dataclass
class AgentConfig:
    agent_path_files: list[str]
    agent_path_directories: list[str]
    agent_config_host: list[Path]


def resolve_agent_config(agent_metadata: AgentMetadata) -> AgentConfig:
    agent_paths = [
        *_ensure_agent_paths(agent_metadata.agent_path_files, True),
        *_ensure_agent_paths(agent_metadata.agent_path_directories, False),
    ]
    return AgentConfig(
        agent_path_files=list(agent_metadata.agent_path_files),
        agent_path_directories=list(agent_metadata.agent_path_directories),
        agent_config_host=agent_paths,
    )


def _ensure_agent_paths(agent_paths: list[str], is_file: bool) -> list[Path]:
    ensured: list[Path] = []
    for agent_path in agent_paths:
        expanded = Path(os.path.expanduser(agent_path)).resolve()
        ensured.append(ensure_path_exists(expanded, is_file))
    return ensured
