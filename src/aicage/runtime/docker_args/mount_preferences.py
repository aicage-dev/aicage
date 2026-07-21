from collections.abc import Callable
from pathlib import Path
from typing import TypeAlias

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

from .support.mount_prompt import MountSelectionPrompt, resolve_mount_prompt_prefs

_ConfirmPreference: TypeAlias = Callable[[], bool]


def apply_mount_preferences(
    context: ConfigContext,
    agent: str,
    parsed: ParsedArgs | None,
    select_mounts: MountSelectionPrompt,
    confirm_persist_docker_socket: _ConfirmPreference,
) -> None:
    agent_cfg = context.project_cfg.agents.setdefault(agent, AgentConfig())
    _apply_git_and_extension_mount_preferences(
        Path(context.project_cfg.path).resolve(),
        agent_cfg,
        context.extensions,
        select_mounts,
    )
    _apply_docker_socket_preference(
        agent_cfg,
        parsed,
        confirm_persist_docker_socket,
    )


def _apply_git_and_extension_mount_preferences(
    project_path: Path,
    agent_cfg: AgentConfig,
    available_extensions: dict[str, ExtensionMetadata],
    select_mounts: MountSelectionPrompt,
) -> None:
    mount_prompt_prefs = resolve_mount_prompt_prefs(
        project_path, agent_cfg, available_extensions, select_mounts
    )
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
    confirm_persist_docker_socket: _ConfirmPreference,
) -> None:
    if (
        parsed is None
        or not parsed.docker_socket
        or getattr(agent_cfg.mounts, MOUNT_DOCKER_KEY) is not None
    ):
        return
    if confirm_persist_docker_socket():
        setattr(agent_cfg.mounts, MOUNT_DOCKER_KEY, True)
