from pathlib import Path

from aicage.paths import container_project_path
from aicage.runtime.docker_args._support._resolver_types import MountRequest
from aicage.runtime.run_args import MountSpec


def map_mount_requests(requests: list[MountRequest]) -> list[MountSpec]:
    deduped_requests = _dedupe_exact_mount_requests(requests)
    selected_requests = _dedupe_nested_mount_requests(deduped_requests)
    return _build_mount_specs(selected_requests)


def _dedupe_exact_mount_requests(requests: list[MountRequest]) -> list[MountRequest]:
    deduped_requests: dict[Path, MountRequest] = {}
    for request in requests:
        host_path = request.host_path.resolve()
        if host_path in deduped_requests:
            continue
        deduped_requests[host_path] = MountRequest(host_path=host_path, read_only=request.read_only)
    return list(deduped_requests.values())


def _dedupe_nested_mount_requests(requests: list[MountRequest]) -> list[MountRequest]:
    selected_requests: list[MountRequest] = []
    for request in requests:
        host_path = request.host_path.resolve()
        if _is_nested_path(host_path, [item.host_path for item in selected_requests]):
            continue
        selected_requests = [item for item in selected_requests if not _is_path_within(item.host_path, host_path)]
        selected_requests.append(request)
    return selected_requests


def _build_mount_specs(requests: list[MountRequest]) -> list[MountSpec]:
    mounts: list[MountSpec] = []
    for request in requests:
        host_path = request.host_path.resolve()
        container_path = container_project_path(host_path)
        mounts.append(
            MountSpec(
                host_path=host_path,
                container_path=container_path,
                read_only=request.read_only,
            )
        )
    return mounts


def _is_nested_path(path: Path, selected_hosts: list[Path]) -> bool:
    for selected in selected_hosts:
        if _is_path_within(path, selected):
            return True
    return False


def _is_path_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False
