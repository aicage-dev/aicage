import os

from aicage.cli_types import ParsedArgs
from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig
from aicage.docker.runtime import get_active_docker_host
from aicage.paths import HOST_DOCKER_SOCKET_PATH
from aicage.runtime.docker_args.support.resolver_types import MountRequest, ResolvedArgs
from aicage.runtime.env_vars import _WINDOWS_DOCKER_HOST, DOCKER_HOST
from aicage.runtime.run_args import EnvVar


def resolve(
    context: ConfigContext,
    agent: str,
    parsed: ParsedArgs | None,
) -> ResolvedArgs:
    agent_cfg: AgentConfig = context.project_cfg.agents[agent]
    mounts_cfg = agent_cfg.mounts
    cli_docker_socket = parsed.docker_socket if parsed else False
    docker_socket_enabled = cli_docker_socket or bool(mounts_cfg.docker)
    if not docker_socket_enabled:
        return ResolvedArgs()

    if os.name == "nt":
        mounts: list[MountRequest] = []
        env = [EnvVar(name=DOCKER_HOST, value=_WINDOWS_DOCKER_HOST)]
    else:
        docker_host = get_active_docker_host()
        mounts = (
            [MountRequest(host_path=docker_host.socket_path)]
            if docker_host.socket_path is not None
            else []
        )
        env = (
            [EnvVar(name=DOCKER_HOST, value=docker_host.host)]
            if docker_host.socket_path != HOST_DOCKER_SOCKET_PATH
            else []
        )

    return ResolvedArgs(mounts=mounts, env=env)
