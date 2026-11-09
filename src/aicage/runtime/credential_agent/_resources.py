"""Credential-sidecar resource orchestration."""

from collections.abc import Iterable
from pathlib import Path

from aicage.docker.execution.client import get_docker_client

from ._resource_lifecycle import (
    _create_container,
    _ensure_ready,
    _ensure_volume,
    _find_container,
    _is_stopped,
    _prepare_volume,
    _requires_replacement,
    _resource_lock,
)
from ._resource_models import (
    _CredentialProtocol,
    _CredentialResource,
    _ImageSpec,
    _resources,
)


def _ensure_resources(
    protocols: Iterable[_CredentialProtocol],
    image_ref: str,
    image_id: str,
    user: str,
    credential_paths: dict[_CredentialProtocol, Path] | None = None,
) -> list[_CredentialResource]:
    requested = _resources(protocols)
    if not requested:
        return []
    credential_paths = credential_paths or {}
    image = _ImageSpec(image_ref=image_ref, image_id=image_id, user=user)
    with _resource_lock():
        client = get_docker_client()
        for resource in requested:
            volume = _ensure_volume(client, resource)
            _prepare_volume(client, resource, volume, image)
            container = _find_container(client, resource)
            credential_path = credential_paths.get(resource.protocol)
            if container is None or _requires_replacement(
                container,
                resource,
                image.image_id,
                credential_path,
            ):
                if container is not None:
                    container.remove(force=True)
                container = _create_container(
                    client, resource, volume, image, credential_path
                )
            elif _is_stopped(container):
                container.start()
            _ensure_ready(client, resource, volume, image.image_ref)
    return requested
