from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

from aicage.cli_types import ParsedArgs
from aicage.errors import AicageError
from aicage.paths import container_project_path
from aicage.runtime._path_utils import ensure_path_exists, looks_like_file
from aicage.runtime.run_args import MountSpec


@dataclass(frozen=True)
class _ShareSpec:
    host_path: Path
    container_path: PurePosixPath
    read_only: bool


def resolve_share_mounts(
    parsed: ParsedArgs,
    project_path: Path,
    existing_mounts: Iterable[MountSpec],
    agent_config_mounts: Iterable[MountSpec],
) -> list[MountSpec]:
    share_mounts: list[MountSpec] = []
    if not parsed.shares:
        return share_mounts
    mounted_hosts = _collect_existing_hosts(project_path, existing_mounts, agent_config_mounts)
    cwd = Path.cwd().resolve()
    for raw in parsed.shares:
        share = _parse_share(raw, cwd)
        if share.host_path in mounted_hosts:
            continue
        mounted_hosts.add(share.host_path)
        share_mounts.append(
            MountSpec(
                host_path=share.host_path,
                container_path=share.container_path,
                read_only=share.read_only,
            )
        )
    return share_mounts


def _parse_share(raw: str, cwd: Path) -> _ShareSpec:
    if not raw:
        raise AicageError("Share value cannot be empty.")
    read_only, host_raw = _parse_read_only(raw)
    if _has_destination_path(host_raw):
        raise AicageError("Share destinations are not supported. Use HOST or HOST:ro.")
    host_path = _resolve_host_path(host_raw, cwd)
    try:
        host_path = ensure_path_exists(host_path, looks_like_file(host_raw))
    except ValueError as exc:
        raise AicageError(str(exc)) from exc
    container_path = _resolve_container_path(host_path)
    return _ShareSpec(host_path=host_path, container_path=container_path, read_only=read_only)


def _parse_read_only(raw: str) -> tuple[bool, str]:
    if raw.endswith(":ro"):
        host_raw = raw[:-3]
        if not host_raw:
            raise AicageError("Share host path cannot be empty.")
        return True, host_raw
    return False, raw


def _resolve_host_path(host_raw: str, cwd: Path) -> Path:
    host_path = Path(host_raw).expanduser()
    if not host_path.is_absolute():
        host_path = cwd / host_path
    return host_path.resolve()


def _resolve_container_path(host_path: Path) -> PurePosixPath:
    return container_project_path(host_path)


def _has_destination_path(host_raw: str) -> bool:
    if ":" not in host_raw:
        return False
    windows_path = PureWindowsPath(host_raw)
    if windows_path.drive and host_raw.startswith(windows_path.drive):
        return host_raw.count(":") > 1
    return True


def _collect_existing_hosts(
    project_path: Path,
    existing_mounts: Iterable[MountSpec],
    agent_config_mounts: Iterable[MountSpec],
) -> set[Path]:
    mounted_hosts = {project_path.resolve()}
    for mount in existing_mounts:
        mounted_hosts.add(mount.host_path.resolve())
    for mount in agent_config_mounts:
        mounted_hosts.add(mount.host_path.resolve())
    return mounted_hosts
