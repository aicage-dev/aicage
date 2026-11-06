"""Docker resources for persistent credential-agent sidecars."""

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath

import portalocker
from docker.client import DockerClient
from docker.errors import DockerException, NotFound
from docker.models.containers import Container
from docker.models.volumes import Volume

from aicage.docker.errors import DockerError
from aicage.docker.execution.client import get_docker_client
from aicage.paths import CREDENTIAL_AGENT_LOCK_PATH

_RESOURCE_LABEL = "org.aicage.resource"
_RESOURCE_VALUE = "credential-agent"
_PROTOCOL_LABEL = "org.aicage.credential-agent.protocol"
_VERSION_LABEL = "org.aicage.credential-agent.version"
_IMAGE_ID_LABEL = "org.aicage.credential-agent.image-id"
_RESOURCE_VERSION = "1"
_LOCK_TIMEOUT_SECONDS = 30


class _CredentialProtocol(StrEnum):
    SSH = "ssh"
    GPG = "gpg"


@dataclass(frozen=True)
class _CredentialResource:
    protocol: _CredentialProtocol
    container_name: str
    volume_name: str
    socket_directory: PurePosixPath
    socket_path: PurePosixPath


@dataclass(frozen=True)
class _ImageSpec:
    image_ref: str
    image_id: str
    user: str


_RESOURCES: dict[_CredentialProtocol, _CredentialResource] = {
    _CredentialProtocol.SSH: _CredentialResource(
        protocol=_CredentialProtocol.SSH,
        container_name="aicage-ssh-agent",
        volume_name="aicage-ssh-agent-socket",
        socket_directory=PurePosixPath("/run/aicage-credential-agent"),
        socket_path=PurePosixPath("/run/aicage-credential-agent/ssh-agent.sock"),
    ),
    _CredentialProtocol.GPG: _CredentialResource(
        protocol=_CredentialProtocol.GPG,
        container_name="aicage-gpg-agent",
        volume_name="aicage-gpg-agent-socket",
        socket_directory=PurePosixPath("/run/aicage-credential-agent"),
        socket_path=PurePosixPath("/run/aicage-credential-agent/S.gpg-agent"),
    ),
}


def _resources(protocols: Iterable[_CredentialProtocol]) -> list[_CredentialResource]:
    return [_RESOURCES[protocol] for protocol in dict.fromkeys(protocols)]


def _ensure_resources(
    protocols: Iterable[_CredentialProtocol],
    image_ref: str,
    image_id: str,
    user: str,
) -> list[_CredentialResource]:
    requested = _resources(protocols)
    if not requested:
        return []
    image = _ImageSpec(image_ref=image_ref, image_id=image_id, user=user)
    with _resource_lock():
        client = get_docker_client()
        for resource in requested:
            volume = _ensure_volume(client, resource)
            _prepare_volume(client, resource, volume, image)
            container = _find_container(client, resource)
            if container is None or _requires_replacement(container, resource, image.image_id):
                if container is not None:
                    container.remove(force=True)
                container = _create_container(
                    client,
                    resource,
                    volume,
                    image,
                )
            elif _is_stopped(container):
                container.start()
            _ensure_ready(client, resource, volume, image.image_ref)
    return requested


def _ensure_volume(client: DockerClient, resource: _CredentialResource) -> Volume:
    try:
        volume = client.volumes.get(resource.volume_name)
    except NotFound:
        volume = client.volumes.create(
            name=resource.volume_name,
            labels=_labels(resource, image_id=None),
        )
    if not _is_owned(volume, resource):
        raise DockerError(f"Credential socket volume '{resource.volume_name}' is not owned by aicage.")
    return volume


def _find_container(
    client: DockerClient,
    resource: _CredentialResource,
) -> Container | None:
    try:
        return client.containers.get(resource.container_name)
    except NotFound:
        return None


def _requires_replacement(
    container: Container,
    resource: _CredentialResource,
    image_id: str,
) -> bool:
    if not _is_owned(container, resource):
        raise DockerError(
            f"Credential sidecar '{resource.container_name}' is not owned by aicage."
        )
    labels = _labels_for(container)
    if labels.get(_VERSION_LABEL) != _RESOURCE_VERSION:
        return True
    if labels.get(_IMAGE_ID_LABEL) != image_id:
        return True
    return _is_unhealthy(container)


def _create_container(
    client: DockerClient,
    resource: _CredentialResource,
    volume: Volume,
    image: _ImageSpec,
) -> Container:
    return client.containers.run(
        image.image_ref,
        [resource.protocol.value, "serve"],
        detach=True,
        name=resource.container_name,
        user=image.user,
        labels=_labels(resource, image_id=image.image_id),
        volumes={
            volume.name: {
                "bind": resource.socket_directory.as_posix(),
                "mode": "rw",
            }
        },
    )


def _prepare_volume(
    client: DockerClient,
    resource: _CredentialResource,
    volume: Volume,
    image: _ImageSpec,
) -> None:
    try:
        client.containers.run(
            image.image_ref,
            ["-c", f"chown {image.user} {resource.socket_directory.as_posix()}"],
            entrypoint="/bin/sh",
            remove=True,
            volumes={
                volume.name: {
                    "bind": resource.socket_directory.as_posix(),
                    "mode": "rw",
                }
            },
        )
    except DockerException as exc:
        raise DockerError(
            f"Failed to prepare credential socket volume '{resource.volume_name}'."
        ) from exc


def _ensure_ready(
    client: DockerClient,
    resource: _CredentialResource,
    volume: Volume,
    image_ref: str,
) -> None:
    try:
        client.containers.run(
            image_ref,
            [resource.protocol.value, "ready"],
            remove=True,
            volumes={
                volume.name: {
                    "bind": resource.socket_directory.as_posix(),
                    "mode": "ro",
                }
            },
        )
    except DockerException as exc:
        raise DockerError(
            f"Credential sidecar '{resource.container_name}' did not become ready."
        ) from exc


def _is_stopped(container: Container) -> bool:
    container.reload()
    return _state_for(container).get("Status") != "running"


def _is_unhealthy(container: Container) -> bool:
    container.reload()
    health = _state_for(container).get("Health")
    return isinstance(health, dict) and health.get("Status") == "unhealthy"


def _is_owned(resource: Container | Volume, expected: _CredentialResource) -> bool:
    labels = _labels_for(resource)
    return (
        labels.get(_RESOURCE_LABEL) == _RESOURCE_VALUE
        and labels.get(_PROTOCOL_LABEL) == expected.protocol.value
    )


def _labels(resource: _CredentialResource, image_id: str | None) -> dict[str, str]:
    labels = {
        _RESOURCE_LABEL: _RESOURCE_VALUE,
        _PROTOCOL_LABEL: resource.protocol.value,
        _VERSION_LABEL: _RESOURCE_VERSION,
    }
    if image_id is not None:
        labels[_IMAGE_ID_LABEL] = image_id
    return labels


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
    if not isinstance(labels, dict):
        return {}
    return {key: value for key, value in labels.items() if isinstance(key, str) and isinstance(value, str)}


def _state_for(container: Container) -> dict[str, object]:
    attrs = getattr(container, "attrs", {})
    state = attrs.get("State", {}) if isinstance(attrs, dict) else {}
    return state if isinstance(state, dict) else {}


@contextmanager
def _resource_lock() -> Iterator[None]:
    CREDENTIAL_AGENT_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with portalocker.Lock(
            str(CREDENTIAL_AGENT_LOCK_PATH),
            timeout=_LOCK_TIMEOUT_SECONDS,
            mode="a+",
        ):
            yield
    except portalocker.exceptions.LockException as exc:
        raise DockerError("Failed to lock credential-agent resources.") from exc
