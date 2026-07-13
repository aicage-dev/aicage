from pathlib import Path

from aicage.paths import container_project_path
from aicage.runtime.docker_args.support.resolver_types import MountRequest
from aicage.runtime.run_args import MountSpec


def map_mount_requests(requests: list[MountRequest]) -> list[MountSpec]:
    deduped_requests = _dedupe_exact_mount_requests(requests)
    # Process shallower paths first so parents are seen before children.
    # That makes nested deduplication one-directional.
    sorted_requests = _sort_mount_requests(deduped_requests)
    selected_requests = _dedupe_nested_mount_requests(sorted_requests)
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
        if any(
            _is_redundant_nested_mount(request, selected, host_path, selected.host_path.resolve())
            for selected in selected_requests
        ):
            continue
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


def _sort_mount_requests(requests: list[MountRequest]) -> list[MountRequest]:
    return sorted(
        requests,
        key=lambda request: (
            len(request.host_path.resolve().parts),
            request.host_path.resolve().as_posix(),
        ),
    )


def _is_redundant_nested_mount(
    nested_request: MountRequest,
    parent_request: MountRequest,
    nested_host_path: Path,
    parent_host_path: Path,
) -> bool:
    return (
        nested_request.read_only == parent_request.read_only
        and _is_path_within(nested_host_path, parent_host_path)
    )


def _is_path_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False
