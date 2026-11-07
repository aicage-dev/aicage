"""Docker lifecycle operations for credential sidecars."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import portalocker
from docker.client import DockerClient
from docker.errors import DockerException, NotFound
from docker.models.containers import Container
from docker.models.volumes import Volume

from aicage.docker.errors import DockerError
from aicage.paths import CREDENTIAL_AGENT_LOCK_PATH

from ._resource_models import (
    _IMAGE_ID_LABEL,
    _PROTOCOL_LABEL,
    _RESOURCE_LABEL,
    _RESOURCE_VALUE,
    _RESOURCE_VERSION,
    _VERSION_LABEL,
    _CredentialResource,
    _ImageSpec,
)

_LOCK_TIMEOUT_SECONDS = 30


def _ensure_volume(client: DockerClient, resource: _CredentialResource) -> Volume:
    try:
        volume = client.volumes.get(resource.volume_name)
    except NotFound:
        volume = client.volumes.create(name=resource.volume_name, labels=_labels(resource, None))
    if not _is_owned(volume, resource):
        raise DockerError(f"Credential socket volume '{resource.volume_name}' is not owned by aicage.")
    return volume


def _find_container(client: DockerClient, resource: _CredentialResource) -> Container | None:
    try:
        return client.containers.get(resource.container_name)
    except NotFound:
        return None


def _requires_replacement(
    container: Container,
    resource: _CredentialResource,
    image_id: str,
    credential_path: Path | None,
) -> bool:
    if not _is_owned(container, resource):
        raise DockerError(f"Credential sidecar '{resource.container_name}' is not owned by aicage.")
    labels = _labels_for(container)
    return (
        labels.get(_VERSION_LABEL) != _RESOURCE_VERSION
        or labels.get(_IMAGE_ID_LABEL) != image_id
        or _credential_mount_path(container, resource) != credential_path
        or _is_unhealthy(container)
    )


def _create_container(
    client: DockerClient,
    resource: _CredentialResource,
    volume: Volume,
    image: _ImageSpec,
    credential_path: Path | None,
) -> Container:
    volumes = {volume.name: {"bind": resource.socket_directory.as_posix(), "mode": "rw"}}
    if credential_path is not None:
        volumes[str(credential_path)] = {"bind": resource.credential_directory.as_posix(), "mode": "ro"}
    return client.containers.run(
        image.image_ref,
        [resource.protocol.value, "serve"],
        detach=True,
        name=resource.container_name,
        user=image.user,
        labels=_labels(resource, image.image_id),
        volumes=volumes,
    )


def _prepare_volume(client: DockerClient, resource: _CredentialResource, volume: Volume, image: _ImageSpec) -> None:
    try:
        client.containers.run(
            image.image_ref,
            ["-c", f"chown {image.user} {resource.socket_directory.as_posix()}"],
            entrypoint="/bin/sh",
            remove=True,
            volumes={volume.name: {"bind": resource.socket_directory.as_posix(), "mode": "rw"}},
        )
    except DockerException as exc:
        raise DockerError(f"Failed to prepare credential socket volume '{resource.volume_name}'.") from exc


def _ensure_ready(client: DockerClient, resource: _CredentialResource, volume: Volume, image_ref: str) -> None:
    try:
        client.containers.run(
            image_ref,
            [resource.protocol.value, "ready"],
            remove=True,
            volumes={volume.name: {"bind": resource.socket_directory.as_posix(), "mode": "ro"}},
        )
    except DockerException as exc:
        raise DockerError(f"Credential sidecar '{resource.container_name}' did not become ready.") from exc


def _is_stopped(container: Container) -> bool:
    container.reload()
    return _state_for(container).get("Status") != "running"


def _labels(resource: _CredentialResource, image_id: str | None) -> dict[str, str]:
    labels = {
        _RESOURCE_LABEL: _RESOURCE_VALUE,
        _PROTOCOL_LABEL: resource.protocol.value,
        _VERSION_LABEL: _RESOURCE_VERSION,
    }
    if image_id is not None:
        labels[_IMAGE_ID_LABEL] = image_id
    return labels


def _is_owned(resource: Container | Volume, expected: _CredentialResource) -> bool:
    labels = _labels_for(resource)
    return labels.get(_RESOURCE_LABEL) == _RESOURCE_VALUE and labels.get(_PROTOCOL_LABEL) == expected.protocol.value


def _is_unhealthy(container: Container) -> bool:
    container.reload()
    health = _state_for(container).get("Health")
    return isinstance(health, dict) and health.get("Status") == "unhealthy"


def _labels_for(resource: Container | Volume) -> dict[str, str]:
    labels = getattr(resource, "labels", None)
    if isinstance(labels, dict):
        return {key: value for key, value in labels.items() if isinstance(key, str) and isinstance(value, str)}
    attrs = getattr(resource, "attrs", {})
    if not isinstance(attrs, dict):
        return {}
    labels = attrs.get("Labels", {})
    if not isinstance(labels, dict):
        config = attrs.get("Config", {})
        labels = config.get("Labels", {}) if isinstance(config, dict) else {}
    return (
        {key: value for key, value in labels.items() if isinstance(key, str) and isinstance(value, str)}
        if isinstance(labels, dict)
        else {}
    )


def _state_for(container: Container) -> dict[str, object]:
    attrs = getattr(container, "attrs", {})
    state = attrs.get("State", {}) if isinstance(attrs, dict) else {}
    return state if isinstance(state, dict) else {}


def _credential_mount_path(container: Container, resource: _CredentialResource) -> Path | None:
    attrs = getattr(container, "attrs", {})
    mounts = attrs.get("Mounts", []) if isinstance(attrs, dict) else []
    if not isinstance(mounts, list):
        return None
    for mount in mounts:
        if isinstance(mount, dict) and mount.get("Destination") == resource.credential_directory.as_posix():
            source = mount.get("Source")
            return Path(source) if isinstance(source, str) else None
    return None


@contextmanager
def _resource_lock() -> Iterator[None]:
    CREDENTIAL_AGENT_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with portalocker.Lock(str(CREDENTIAL_AGENT_LOCK_PATH), timeout=_LOCK_TIMEOUT_SECONDS, mode="a+"):
            yield
    except portalocker.exceptions.LockException as exc:
        raise DockerError("Failed to lock credential-agent resources.") from exc
