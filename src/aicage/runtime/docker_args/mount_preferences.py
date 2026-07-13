from pathlib import Path

from aicage.cli_types import ParsedArgs
from aicage.config.context import ConfigContext
from aicage.config.extensions.loader import ExtensionMetadata
from aicage.config.project_config import (
    MOUNT_DOCKER_KEY,
    MOUNT_GITCONFIG_KEY,
    MOUNT_GITROOT_KEY,
    MOUNT_GNUPG_KEY,
    MOUNT_SSH_KEY,
    AgentConfig,
)
from aicage.runtime.prompts.confirm import prompt_persist_docker_socket

from .support.mount_prompt import resolve_mount_prompt_prefs


def apply_mount_preferences(
    context: ConfigContext,
    agent: str,
    parsed: ParsedArgs | None,
) -> None:
    agent_cfg = context.project_cfg.agents.setdefault(agent, AgentConfig())
    _apply_git_and_extension_mount_preferences(
        Path(context.project_cfg.path).resolve(),
        agent_cfg,
        context.extensions,
    )
    _apply_docker_socket_preference(agent_cfg, parsed)


def _apply_git_and_extension_mount_preferences(
    project_path: Path,
    agent_cfg: AgentConfig,
    available_extensions: dict[str, ExtensionMetadata],
) -> None:
    mount_prompt_prefs = resolve_mount_prompt_prefs(project_path, agent_cfg, available_extensions)
    if mount_prompt_prefs is None:
        return
    for key in (
        MOUNT_GITCONFIG_KEY,
        MOUNT_GITROOT_KEY,
        MOUNT_GNUPG_KEY,
        MOUNT_SSH_KEY,
    ):
        if getattr(agent_cfg.mounts, key) is None:
            setattr(agent_cfg.mounts, key, key in mount_prompt_prefs.git_mounts)
    agent_cfg.extension_mounts.update(mount_prompt_prefs.extension_mounts)


def _apply_docker_socket_preference(
    agent_cfg: AgentConfig,
    parsed: ParsedArgs | None,
) -> None:
    if parsed is None or not parsed.docker_socket or getattr(agent_cfg.mounts, MOUNT_DOCKER_KEY) is not None:
        return
    if prompt_persist_docker_socket():
        setattr(agent_cfg.mounts, MOUNT_DOCKER_KEY, True)
