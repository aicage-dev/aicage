"""Protocol-aware credential forwarding for target containers."""

import os
import subprocess  # nosec B404 -- credential-agent readiness requires fixed host commands.
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from shutil import which

from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig
from aicage.docker.execution.env import resolve_container_user
from aicage.paths import HOST_SSH_DIR, container_project_path
from aicage.reporting import OperationReporter
from aicage.runtime._ssh_agent import (
    _agent_is_reachable,
    _resolve_ssh_agent_socket,
    _resolve_ssh_key_files,
    _resolve_ssh_support_files,
)
from aicage.runtime.docker_args.support.git_support import (
    resolve_gpg_agent_extra_socket,
    resolve_gpg_home,
    resolve_gpg_public_files,
)
from aicage.runtime.docker_args.support.signing import (
    is_commit_signing_enabled,
    resolve_signing_format,
)
from aicage.runtime.run_args import EnvVar, MountSpec, VolumeMountSpec

from ._resources import _CredentialProtocol, _CredentialResource
from ._sidecars import _ensure_sidecars

_SSH_AUTH_SOCK = "SSH_AUTH_SOCK"
_GNUPGHOME = "GNUPGHOME"
_SSH_SOCKET_DIRECTORY = PurePosixPath("/run/aicage-credential-agent")
_SSH_SOCKET = _SSH_SOCKET_DIRECTORY / "ssh-agent.sock"
_GPG_SOCKET_NAME = "S.gpg-agent"
_GPG_CONNECT_AGENT = which("gpg-connect-agent")


@contextmanager
def forwarding(
    context: ConfigContext,
    agent: str,
    reporter: OperationReporter,
) -> Iterator[tuple[list[MountSpec | VolumeMountSpec], list[EnvVar]]]:
    agent_cfg = context.project_cfg.agents.get(agent, AgentConfig())
    mounts: list[MountSpec | VolumeMountSpec] = []
    env: list[EnvVar] = []
    sidecar_protocols: list[_CredentialProtocol] = []
    credential_paths: dict[_CredentialProtocol, Path] = {}

    if agent_cfg.mounts.ssh is True:
        ssh_mounts, ssh_env, ssh_sidecar = _ssh_forwarding()
        mounts.extend(ssh_mounts)
        env.extend(ssh_env)
        if ssh_sidecar:
            sidecar_protocols.append(_CredentialProtocol.SSH)
            if HOST_SSH_DIR.is_dir():
                credential_paths[_CredentialProtocol.SSH] = HOST_SSH_DIR

    if _gpg_enabled(context, agent):
        gpg_mounts, gpg_env, gpg_sidecar, gpg_home = _gpg_forwarding()
        mounts.extend(gpg_mounts)
        env.extend(gpg_env)
        if gpg_sidecar:
            sidecar_protocols.append(_CredentialProtocol.GPG)
            if gpg_home is not None:
                credential_paths[_CredentialProtocol.GPG] = gpg_home

    resources = _ensure_sidecars(
        sidecar_protocols,
        resolve_container_user(),
        reporter,
        credential_paths,
    )
    for resource in resources:
        _append_sidecar_target_args(resource, mounts, env)
    yield mounts, env


def ensure_ssh_setup(
    context: ConfigContext,
    agent: str,
    reporter: OperationReporter,
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
    _ensure_sidecars(
        [_CredentialProtocol.SSH],
        resolve_container_user(),
        reporter,
        credential_paths,
    )


def _ssh_forwarding() -> tuple[list[MountSpec], list[EnvVar], bool]:
    socket = _direct_ssh_socket()
    support_mounts = _ssh_support_mounts()
    if socket is not None:
        return (
            [
                MountSpec(
                    host_path=socket,
                    container_path=_SSH_SOCKET,
                ),
                *support_mounts,
            ],
            [EnvVar(name=_SSH_AUTH_SOCK, value=_SSH_SOCKET.as_posix())],
            False,
        )
    if not _resolve_ssh_key_files() and not HOST_SSH_DIR.is_dir():
        return support_mounts, [], False
    return support_mounts, [], True


def _direct_ssh_socket() -> Path | None:
    if os.name == "nt":
        return None
    socket = _resolve_ssh_agent_socket()
    if socket is None or not socket.is_socket():
        return None
    env = {**os.environ, _SSH_AUTH_SOCK: str(socket)}
    return socket if _agent_is_reachable(env) else None


def _ssh_support_mounts() -> list[MountSpec]:
    return [
        MountSpec(
            host_path=path,
            container_path=container_project_path(path),
            read_only=True,
        )
        for path in _resolve_ssh_support_files()
    ]


def _gpg_enabled(context: ConfigContext, agent: str) -> bool:
    agent_cfg = context.project_cfg.agents.get(agent, AgentConfig())
    project_path = Path(context.project_cfg.path)
    return (
        agent_cfg.mounts.gnupg is True
        and is_commit_signing_enabled(project_path)
        and resolve_signing_format(project_path) != "ssh"
    )


def _gpg_forwarding() -> tuple[list[MountSpec], list[EnvVar], bool, Path | None]:
    gpg_home = resolve_gpg_home()
    if gpg_home is None:
        return [], [], False, None
    container_home = container_project_path(gpg_home)
    support_mounts = [
        MountSpec(
            host_path=path, container_path=container_project_path(path), read_only=True
        )
        for path in resolve_gpg_public_files(gpg_home)
    ]
    socket = _direct_gpg_socket()
    env = [EnvVar(name=_GNUPGHOME, value=container_home.as_posix())]
    if socket is not None:
        return (
            [
                MountSpec(
                    host_path=socket,
                    container_path=container_home / _GPG_SOCKET_NAME,
                ),
                *support_mounts,
            ],
            env,
            False,
            gpg_home,
        )
    return support_mounts, env, True, gpg_home


def _direct_gpg_socket() -> Path | None:
    if os.name == "nt":
        return None
    socket = resolve_gpg_agent_extra_socket()
    if socket is None or _GPG_CONNECT_AGENT is None or not socket.is_socket():
        return None
    result = subprocess.run(  # nosec B603 -- fixed GnuPG readiness probe.
        [_GPG_CONNECT_AGENT, "--raw-socket", str(socket), "/bye"],
        check=False,
        capture_output=True,
        text=True,
    )
    return socket if result.returncode == 0 else None


def _append_sidecar_target_args(
    resource: _CredentialResource,
    mounts: list[MountSpec | VolumeMountSpec],
    env: list[EnvVar],
) -> None:
    if resource.protocol is _CredentialProtocol.SSH:
        mounts.append(
            VolumeMountSpec(
                volume_name=resource.volume_name,
                container_path=_SSH_SOCKET_DIRECTORY,
                read_only=True,
            )
        )
        env.append(EnvVar(name=_SSH_AUTH_SOCK, value=_SSH_SOCKET.as_posix()))
        return
    gpg_env = next(item for item in env if item.name == _GNUPGHOME)
    mounts.append(
        VolumeMountSpec(
            volume_name=resource.volume_name,
            container_path=PurePosixPath(gpg_env.value),
            read_only=True,
        )
    )
