"""Protocol-aware credential forwarding for target containers."""

from collections.abc import Iterator
from contextlib import contextmanager
from functools import partial

from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig
from aicage.docker.execution.env import resolve_container_user
from aicage.reporting import OperationReporter
from aicage.runtime.run_args import EnvVar, MountSpec

from ._gpg_forwarding import (
    _gpg_enabled,
    _gpg_forwarding,
    _GpgForwardingPlan,
    _reload_gpg_keys,
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
    gpg_plan: _GpgForwardingPlan | None = None

    if agent_cfg.mounts.ssh is True:
        ssh_mounts, ssh_env, ssh_sidecar = _ssh_forwarding()
        mounts.extend(ssh_mounts)
        env.extend(ssh_env)
        if ssh_sidecar:
            protocols.append(_CredentialProtocol.SSH)

    if _gpg_enabled(context, agent):
        gpg_plan = _gpg_forwarding()
        if gpg_plan is not None:
            mounts.extend(gpg_plan.target_mounts)
            env.extend(gpg_plan.target_env)
        if gpg_plan is not None and gpg_plan.requires_sidecar:
            protocols.append(_CredentialProtocol.GPG)

    resources = _ensure_sidecars(
        protocols,
        resolve_container_user(),
        reporter,
        gpg_plan.credential_home if gpg_plan is not None else None,
        reconcile=partial(_reload_credentials, interactive=False),
    )
    gpg_resource: _CredentialResource | None = None
    for resource in resources:
        if resource.protocol is _CredentialProtocol.GPG:
            gpg_resource = resource
        else:
            _append_sidecar_target_args(resource, mounts, env)
    if gpg_resource is None or gpg_plan is None:
        yield mounts, env
        return
    with gpg_plan.sidecar_target_args(gpg_resource) as (
        sidecar_mounts,
        sidecar_env,
    ):
        mounts.extend(sidecar_mounts)
        env.extend(sidecar_env)
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
    _ensure_sidecars(
        [_CredentialProtocol.SSH],
        resolve_container_user(),
        reporter,
        reconcile=partial(_reload_credentials, interactive=interactive),
    )


def ensure_gpg_setup(
    context: ConfigContext,
    agent: str,
    reporter: OperationReporter,
    *,
    interactive: bool,
) -> None:
    if not _gpg_enabled(context, agent):
        return
    gpg_plan = _gpg_forwarding()
    if gpg_plan is None or not gpg_plan.requires_sidecar:
        return
    _ensure_sidecars(
        [_CredentialProtocol.GPG],
        resolve_container_user(),
        reporter,
        gpg_plan.credential_home,
        reconcile=partial(_reload_credentials, interactive=interactive),
    )


def _reload_credentials(
    resources: list[_CredentialResource], *, interactive: bool
) -> None:
    _reload_ssh_keys(resources, interactive=interactive)
    _reload_gpg_keys(resources, interactive=interactive)


def _append_sidecar_target_args(
    resource: _CredentialResource,
    mounts: list[MountSpec],
    env: list[EnvVar],
) -> None:
    if resource.protocol is _CredentialProtocol.SSH:
        _append_ssh_target_args(resource, mounts, env)
