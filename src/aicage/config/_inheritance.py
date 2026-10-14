from copy import deepcopy
from pathlib import Path

from .config_store import SettingsStore
from .project_config import AgentConfig, _AgentMounts, _ProjectConfig


def load_effective_project_config(
    store: SettingsStore,
    project_path: Path,
    local_config: _ProjectConfig,
) -> _ProjectConfig:
    configs = [store.load_global()]
    configs.extend(
        store.load_tree(path)
        for path in [*reversed(project_path.parents), project_path]
    )
    return merge_project_configs([*configs, local_config], project_path)


def merge_project_configs(
    configs: list[_ProjectConfig],
    project_path: Path,
) -> _ProjectConfig:
    result = _ProjectConfig(path=str(project_path))
    for config in configs:
        for agent, agent_config in config.agents.items():
            result.agents[agent] = _merge_agent_configs(
                result.agents.get(agent), agent_config
            )
    return result


def merge_agent_configs(
    inherited: AgentConfig | None,
    local: AgentConfig,
) -> AgentConfig:
    return _merge_agent_configs(inherited, local)


def rebase_agent_config(
    effective: AgentConfig,
    inherited: AgentConfig | None,
) -> AgentConfig:
    inherited_config = inherited or AgentConfig()
    return AgentConfig(
        base=effective.base if effective.base != inherited_config.base else None,
        docker_args=_local_docker_args(
            effective.docker_args, inherited_config.docker_args
        ),
        mounts=_local_mounts(effective.mounts, inherited_config.mounts),
        image_ref=(
            effective.image_ref
            if effective.image_ref != inherited_config.image_ref
            else None
        ),
        extensions=[
            extension
            for extension in effective.extensions
            if extension not in inherited_config.extensions
        ],
        shares=_local_shares(effective.shares, inherited_config.shares),
        extension_mounts={
            key: value
            for key, value in effective.extension_mounts.items()
            if inherited_config.extension_mounts.get(key) != value
        },
    )


def _merge_agent_configs(
    inherited: AgentConfig | None,
    local: AgentConfig,
) -> AgentConfig:
    result = deepcopy(inherited) if inherited is not None else AgentConfig()
    if local.base is not None:
        result.base = local.base
        result.image_ref = None
    if local.docker_args:
        result.docker_args = " ".join(
            value for value in [result.docker_args, local.docker_args] if value
        )
    result.mounts = _merge_mounts(result.mounts, local.mounts)
    if local.image_ref is not None:
        result.image_ref = local.image_ref
    result.extensions = _merge_extension_ids(result.extensions, local.extensions)
    if local.extensions and local.image_ref is None:
        result.image_ref = None
    result.shares.extend(local.shares)
    result.extension_mounts.update(local.extension_mounts)
    return result


def _merge_mounts(
    inherited: _AgentMounts,
    local: _AgentMounts,
) -> _AgentMounts:
    return _AgentMounts(
        **{
            name: (
                getattr(local, name)
                if getattr(local, name) is not None
                else getattr(inherited, name)
            )
            for name in ("gitconfig", "gitroot", "gnupg", "ssh", "docker")
        }
    )


def _local_docker_args(effective: str, inherited: str) -> str:
    if not inherited:
        return effective
    prefix = f"{inherited} "
    if effective.startswith(prefix):
        return effective.removeprefix(prefix)
    return effective


def _local_mounts(
    effective: _AgentMounts,
    inherited: _AgentMounts,
) -> _AgentMounts:
    return _AgentMounts(
        **{
            name: (
                getattr(effective, name)
                if getattr(effective, name) != getattr(inherited, name)
                else None
            )
            for name in ("gitconfig", "gitroot", "gnupg", "ssh", "docker")
        }
    )


def _local_shares(effective: list[str], inherited: list[str]) -> list[str]:
    if effective[: len(inherited)] == inherited:
        return effective[len(inherited) :]
    return effective


def _merge_extension_ids(
    inherited: list[str],
    local: list[str],
) -> list[str]:
    return list(dict.fromkeys([*inherited, *local]))
