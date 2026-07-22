from pathlib import Path
from typing import Any

from aicage.config._base_exclude import is_base_excluded, normalize_exclude
from aicage.config._yaml import (
    expect_bool,
    expect_keys,
    expect_string,
    maybe_str_list,
    read_str_list,
)
from aicage.config.agent._validation import validate_agent_mapping
from aicage.config.agent.models import (
    _AGENT_FULL_NAME_KEY,
    _AGENT_HOMEPAGE_KEY,
    _AGENT_PATH_DIRECTORIES_KEY,
    _AGENT_PATH_FILES_KEY,
    _AGENT_PATH_KEY,
    _BASE_DISTRO_EXCLUDE_KEY,
    _BASE_EXCLUDE_KEY,
    _BUILD_LOCAL_KEY,
    AgentMetadata,
)
from aicage.config.base.architecture import base_supports_host_architecture
from aicage.config.base.models import BaseMetadata
from aicage.config.errors import ConfigError
from aicage.config.image_refs import local_image_ref
from aicage.constants import IMAGE_REGISTRY, IMAGE_REPOSITORY, LOCAL_IMAGE_REPOSITORY


def build_agent_metadata(
    agent_name: str,
    agent_mapping: dict[str, Any],
    bases: dict[str, BaseMetadata],
    definition_dir: Path,
) -> AgentMetadata:
    normalized_mapping = validate_agent_mapping(agent_mapping)
    agent_path = _read_agent_path(normalized_mapping)
    base_exclude = (
        maybe_str_list(normalized_mapping.get(_BASE_EXCLUDE_KEY), _BASE_EXCLUDE_KEY)
        or []
    )
    base_distro_exclude = (
        maybe_str_list(
            normalized_mapping.get(_BASE_DISTRO_EXCLUDE_KEY), _BASE_DISTRO_EXCLUDE_KEY
        )
        or []
    )
    build_local = expect_bool(
        normalized_mapping.get(_BUILD_LOCAL_KEY), _BUILD_LOCAL_KEY
    )
    valid_bases = _build_valid_bases(
        agent_name=agent_name,
        bases=bases,
        base_exclude=base_exclude,
        base_distro_exclude=base_distro_exclude,
        build_local=build_local,
    )
    return AgentMetadata(
        agent_path_files=agent_path.files,
        agent_path_directories=agent_path.directories,
        agent_full_name=expect_string(
            normalized_mapping.get(_AGENT_FULL_NAME_KEY), _AGENT_FULL_NAME_KEY
        ),
        agent_homepage=expect_string(
            normalized_mapping.get(_AGENT_HOMEPAGE_KEY), _AGENT_HOMEPAGE_KEY
        ),
        build_local=build_local,
        valid_bases=valid_bases,
        base_exclude=base_exclude,
        base_distro_exclude=base_distro_exclude,
        local_definition_dir=definition_dir,
    )


class _AgentPath:
    def __init__(self, files: list[str], directories: list[str]) -> None:
        self.files = files
        self.directories = directories


def _read_agent_path(mapping: dict[str, Any]) -> _AgentPath:
    raw = mapping.get(_AGENT_PATH_KEY)
    if raw is None:
        return _AgentPath(files=[], directories=[])
    if not isinstance(raw, dict):
        raise ConfigError(f"{_AGENT_PATH_KEY} must be a mapping.")
    expect_keys(
        raw,
        required=set(),
        optional={_AGENT_PATH_FILES_KEY, _AGENT_PATH_DIRECTORIES_KEY},
        context=_AGENT_PATH_KEY,
    )
    files = read_str_list(
        raw.get(_AGENT_PATH_FILES_KEY, []),
        f"{_AGENT_PATH_KEY}.{_AGENT_PATH_FILES_KEY}",
    )
    directories = read_str_list(
        raw.get(_AGENT_PATH_DIRECTORIES_KEY, []),
        f"{_AGENT_PATH_KEY}.{_AGENT_PATH_DIRECTORIES_KEY}",
    )
    return _AgentPath(files=files, directories=directories)


def _build_valid_bases(
    agent_name: str,
    bases: dict[str, BaseMetadata],
    base_exclude: list[str],
    base_distro_exclude: list[str],
    build_local: bool,
) -> dict[str, str]:
    valid_bases: dict[str, str] = {}
    base_exclude_set = normalize_exclude(base_exclude)
    base_distro_exclude_set = normalize_exclude(base_distro_exclude)
    repository = _image_repository(build_local)
    for base_name in sorted(bases):
        base_metadata = bases[base_name]
        if is_base_excluded(
            base_name,
            base_metadata.base_image_distro,
            base_exclude_set,
            base_distro_exclude_set,
        ):
            continue
        if not base_supports_host_architecture(base_metadata.architectures):
            continue
        valid_bases[base_name] = local_image_ref(repository, agent_name, base_name)
    return valid_bases


def _image_repository(build_local: bool) -> str:
    if build_local:
        return LOCAL_IMAGE_REPOSITORY
    return f"{IMAGE_REGISTRY}/{IMAGE_REPOSITORY}"
