"""Protocol-aware credential forwarding for target containers."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig
from aicage.docker.execution.env import resolve_container_user
from aicage.paths import HOST_SSH_DIR
from aicage.reporting import OperationReporter
from aicage.runtime.run_args import EnvVar, MountSpec, VolumeMountSpec

from ._gpg_forwarding import _append_gpg_target_args, _gpg_enabled, _gpg_forwarding
from ._resource_models import _CredentialProtocol, _CredentialResource
from ._sidecars import _ensure_sidecars
from ._ssh_forwarding import (
    _append_ssh_target_args,
    _reload_ssh_keys,
    _ssh_forwarding,
)


@contextmanager
def forwarding(
    context: ConfigContext,
    agent: str,
    reporter: OperationReporter,
) -> Iterator[tuple[list[MountSpec | VolumeMountSpec], list[EnvVar]]]:
    agent_cfg = context.project_cfg.agents.get(agent, AgentConfig())
    mounts: list[MountSpec | VolumeMountSpec] = []
    env: list[EnvVar] = []
    protocols: list[_CredentialProtocol] = []
    credential_paths: dict[_CredentialProtocol, Path] = {}

    if agent_cfg.mounts.ssh is True:
        ssh_mounts, ssh_env, ssh_sidecar = _ssh_forwarding()
        mounts.extend(ssh_mounts)
        env.extend(ssh_env)
        if ssh_sidecar:
            protocols.append(_CredentialProtocol.SSH)
            if HOST_SSH_DIR.is_dir():
                credential_paths[_CredentialProtocol.SSH] = HOST_SSH_DIR

    if _gpg_enabled(context, agent):
        gpg_mounts, gpg_env, gpg_sidecar, gpg_home = _gpg_forwarding()
        mounts.extend(gpg_mounts)
        env.extend(gpg_env)
        if gpg_sidecar:
            protocols.append(_CredentialProtocol.GPG)
            if gpg_home is not None:
                credential_paths[_CredentialProtocol.GPG] = gpg_home

    resources = _ensure_sidecars(
        protocols, resolve_container_user(), reporter, credential_paths
    )
    for resource in resources:
        _append_sidecar_target_args(resource, mounts, env)
    _reload_ssh_keys(resources, interactive=False)
    yield mounts, env


def ensure_ssh_setup(
    context: ConfigContext,
    agent: str,
    reporter: OperationReporter,
    *,
    interactive: bool,
) -> None:
    agent_cfg = context.project_cfg.agents.get(agent, AgentConfig())
    if agent_cfg.mounts.ssh is not True:
        return
    _mounts, _env, sidecar = _ssh_forwarding()
    if not sidecar:
        return
    credential_paths: dict[_CredentialProtocol, Path] = {}
    if HOST_SSH_DIR.is_dir():
        credential_paths[_CredentialProtocol.SSH] = HOST_SSH_DIR
    resources = _ensure_sidecars(
        [_CredentialProtocol.SSH],
        resolve_container_user(),
        reporter,
        credential_paths,
    )
    _reload_ssh_keys(resources, interactive=interactive)


def _append_sidecar_target_args(
    resource: _CredentialResource,
    mounts: list[MountSpec | VolumeMountSpec],
    env: list[EnvVar],
) -> None:
    if resource.protocol is _CredentialProtocol.SSH:
        _append_ssh_target_args(resource, mounts, env)
        return
    _append_gpg_target_args(resource, mounts, env)
