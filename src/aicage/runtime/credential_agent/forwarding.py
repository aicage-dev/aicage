"""Protocol-aware credential forwarding for target containers."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig
from aicage.docker.execution.env import resolve_container_user
from aicage.reporting import OperationReporter
from aicage.runtime.run_args import EnvVar, MountSpec

from ._gpg_forwarding import (
    _gpg_enabled,
    _gpg_forwarding,
    _gpg_sidecar_target_args,
)
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
) -> Iterator[tuple[list[MountSpec], list[EnvVar]]]:
    agent_cfg = context.project_cfg.agents.get(agent, AgentConfig())
    mounts: list[MountSpec] = []
    env: list[EnvVar] = []
    protocols: list[_CredentialProtocol] = []
    gpg_home: Path | None = None

    if agent_cfg.mounts.ssh is True:
        ssh_mounts, ssh_env, ssh_sidecar = _ssh_forwarding()
        mounts.extend(ssh_mounts)
        env.extend(ssh_env)
        if ssh_sidecar:
            protocols.append(_CredentialProtocol.SSH)

    if _gpg_enabled(context, agent):
        gpg_mounts, gpg_env, gpg_sidecar, gpg_home = _gpg_forwarding()
        mounts.extend(gpg_mounts)
        env.extend(gpg_env)
        if gpg_sidecar:
            protocols.append(_CredentialProtocol.GPG)

    resources = _ensure_sidecars(protocols, resolve_container_user(), reporter, gpg_home)
    gpg_resource: _CredentialResource | None = None
    for resource in resources:
        if resource.protocol is _CredentialProtocol.GPG:
            gpg_resource = resource
        else:
            _append_sidecar_target_args(resource, mounts, env)
    if gpg_resource is None or gpg_home is None:
        _reload_ssh_keys(resources, interactive=False)
        yield mounts, env
        return
    with _gpg_sidecar_target_args(gpg_resource, gpg_home) as (
        sidecar_mounts,
        sidecar_env,
    ):
        mounts.extend(sidecar_mounts)
        env.extend(sidecar_env)
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
    resources = _ensure_sidecars(
        [_CredentialProtocol.SSH],
        resolve_container_user(),
        reporter,
    )
    _reload_ssh_keys(resources, interactive=interactive)


def _append_sidecar_target_args(
    resource: _CredentialResource,
    mounts: list[MountSpec],
    env: list[EnvVar],
) -> None:
    if resource.protocol is _CredentialProtocol.SSH:
        _append_ssh_target_args(resource, mounts, env)
