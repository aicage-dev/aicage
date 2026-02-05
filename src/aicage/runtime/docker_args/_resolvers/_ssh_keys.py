from pathlib import Path

from aicage.cli_types import ParsedArgs
from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig
from aicage.runtime.docker_args._support._resolver_types import MountRequest, ResolvedArgs

from .._support._git_support import resolve_ssh_dir
from .._support._signing import is_commit_signing_enabled, resolve_signing_format


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
    if resolve_signing_format(project_path) != "ssh":
        return ResolvedArgs()

    ssh_dir = resolve_ssh_dir()
    if not ssh_dir.exists():
        return ResolvedArgs()

    mounts_cfg = agent_cfg.mounts
    if mounts_cfg.ssh:
        return ResolvedArgs(mounts=[MountRequest(host_path=ssh_dir)])
    return ResolvedArgs()
