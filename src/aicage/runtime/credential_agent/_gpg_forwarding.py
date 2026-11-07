"""GnuPG credential-forwarding operations."""

import os
import subprocess  # nosec B404 -- GnuPG readiness uses a fixed host command.
from pathlib import Path, PurePosixPath
from shutil import which

from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig
from aicage.paths import container_project_path
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

from ._resource_models import _CredentialResource

_GNUPGHOME = "GNUPGHOME"
_GPG_SOCKET_NAME = "S.gpg-agent"
_GPG_CONNECT_AGENT = which("gpg-connect-agent")


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
        MountSpec(path, container_project_path(path), True)
        for path in resolve_gpg_public_files(gpg_home)
    ]
    env = [EnvVar(_GNUPGHOME, container_home.as_posix())]
    socket = _direct_gpg_socket()
    if socket is not None:
        return (
            [MountSpec(socket, container_home / _GPG_SOCKET_NAME), *support_mounts],
            env,
            False,
            gpg_home,
        )
    return support_mounts, env, True, gpg_home


def _append_gpg_target_args(
    resource: _CredentialResource,
    mounts: list[MountSpec | VolumeMountSpec],
    env: list[EnvVar],
) -> None:
    gpg_env = next(item for item in env if item.name == _GNUPGHOME)
    mounts.append(
        VolumeMountSpec(resource.volume_name, PurePosixPath(gpg_env.value))
    )


def _direct_gpg_socket() -> Path | None:
    if os.name == "nt":
        return None
    socket = resolve_gpg_agent_extra_socket()
    if socket is None or _GPG_CONNECT_AGENT is None or not socket.is_socket():
        return None
    result = subprocess.run(
        [_GPG_CONNECT_AGENT, "--raw-socket", str(socket), "/bye"],
        check=False,
        capture_output=True,
        text=True,
    )  # nosec B603
    return socket if result.returncode == 0 else None
