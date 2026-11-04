from pathlib import Path, PurePosixPath

from aicage.cli_types import ParsedArgs
from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig
from aicage.runtime.docker_args.support.git_support import (
    resolve_ssh_agent_socket,
    resolve_ssh_support_files,
    uses_ssh_remotes,
)
from aicage.runtime.docker_args.support.resolver_types import MountRequest, ResolvedArgs
from aicage.runtime.docker_args.support.signing import (
    is_commit_signing_enabled,
    resolve_signing_format,
)
from aicage.runtime.run_args import EnvVar

_CONTAINER_SSH_AGENT_SOCKET = PurePosixPath("/run/aicage-ssh-agent.sock")
_SSH_AUTH_SOCK = "SSH_AUTH_SOCK"


def resolve(
    context: ConfigContext,
    agent: str,
    parsed: ParsedArgs | None,
) -> ResolvedArgs:
    _ = parsed
    project_path = Path(context.project_cfg.path)
    agent_cfg: AgentConfig = context.project_cfg.agents[agent]
    signing_enabled = is_commit_signing_enabled(project_path)
    signing_format = resolve_signing_format(project_path) if signing_enabled else None
    ssh_needed = (signing_enabled and signing_format == "ssh") or uses_ssh_remotes(
        project_path
    )
    if not ssh_needed:
        return ResolvedArgs()

    ssh_agent_socket = resolve_ssh_agent_socket()
    if ssh_agent_socket is None:
        return ResolvedArgs()

    mounts_cfg = agent_cfg.mounts
    if mounts_cfg.ssh:
        mounts = [
            MountRequest(
                host_path=ssh_agent_socket,
                container_path=_CONTAINER_SSH_AGENT_SOCKET,
            )
        ]
        mounts.extend(
            MountRequest(host_path=path, read_only=True)
            for path in resolve_ssh_support_files()
        )
        return ResolvedArgs(
            mounts=mounts,
            env=[
                EnvVar(
                    name=_SSH_AUTH_SOCK,
                    value=_CONTAINER_SSH_AGENT_SOCKET.as_posix(),
                )
            ],
        )
    return ResolvedArgs()
