from pathlib import Path

from aicage.cli_types import ParsedArgs
from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig
from aicage.paths import container_project_path
from aicage.runtime.docker_args.support.git_support import (
    resolve_gpg_agent_extra_socket,
    resolve_gpg_home,
    resolve_gpg_public_files,
)
from aicage.runtime.docker_args.support.resolver_types import MountRequest, ResolvedArgs
from aicage.runtime.docker_args.support.signing import (
    is_commit_signing_enabled,
    resolve_signing_format,
)
from aicage.runtime.run_args import EnvVar

_GPG_AGENT_SOCKET_NAME = "S.gpg-agent"
_GNUPGHOME = "GNUPGHOME"


def resolve(
    context: ConfigContext,
    agent: str,
    parsed: ParsedArgs | None,
) -> ResolvedArgs:
    _ = parsed
    project_path = Path(context.project_cfg.path)
    agent_cfg: AgentConfig = context.project_cfg.agents[agent]
    if not is_commit_signing_enabled(project_path):
        return ResolvedArgs()
    if resolve_signing_format(project_path) == "ssh":
        return ResolvedArgs()

    gpg_home = resolve_gpg_home()
    gpg_agent_socket = resolve_gpg_agent_extra_socket()
    if not gpg_home or not gpg_agent_socket:
        return ResolvedArgs()

    mounts_cfg = agent_cfg.mounts
    if mounts_cfg.gnupg:
        container_gpg_home = container_project_path(gpg_home)
        mounts = [
            MountRequest(
                host_path=gpg_agent_socket,
                container_path=container_gpg_home / _GPG_AGENT_SOCKET_NAME,
            )
        ]
        mounts.extend(
            MountRequest(host_path=path, read_only=True)
            for path in resolve_gpg_public_files(gpg_home)
        )
        return ResolvedArgs(
            mounts=mounts,
            env=[EnvVar(name=_GNUPGHOME, value=container_gpg_home.as_posix())],
        )
    return ResolvedArgs()
