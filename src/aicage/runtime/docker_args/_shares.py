from pathlib import Path

from aicage.cli_types import ParsedArgs
from aicage.config.context import ConfigContext
from aicage.runtime.docker_args._resolver_types import MountRequest, ResolvedArgs
from aicage.runtime.mounts.shares import ShareSpec, resolve_share_mounts


def resolve(
    context: ConfigContext,
    agent: str,
    parsed: ParsedArgs | None,
) -> ResolvedArgs:
    _ = (context, agent)
    if parsed is None:
        return ResolvedArgs()
    cwd = Path.cwd().resolve()
    share_mounts: list[ShareSpec] = resolve_share_mounts(parsed, cwd)
    mounts = [MountRequest(host_path=share.host_path, read_only=share.read_only) for share in share_mounts]
    return ResolvedArgs(mounts=mounts)
