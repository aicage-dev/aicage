from dataclasses import dataclass, field
from pathlib import Path

_AGENT_PATH_KEY: str = "agent_path"
_AGENT_PATH_FILES_KEY: str = "files"
_AGENT_PATH_DIRECTORIES_KEY: str = "directories"
_AGENT_FULL_NAME_KEY: str = "agent_full_name"
_AGENT_HOMEPAGE_KEY: str = "agent_homepage"
_BUILD_LOCAL_KEY: str = "build_local"
_BASE_EXCLUDE_KEY: str = "base_exclude"
_BASE_DISTRO_EXCLUDE_KEY: str = "base_distro_exclude"


@dataclass(frozen=True)
class AgentMetadata:
    agent_path_files: list[str]
    agent_path_directories: list[str]
    agent_full_name: str
    agent_homepage: str
    build_local: bool
    valid_bases: dict[str, str]
    local_definition_dir: Path
    base_exclude: list[str] = field(default_factory=list)
    base_distro_exclude: list[str] = field(default_factory=list)
