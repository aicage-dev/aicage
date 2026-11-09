"""GnuPG key loading through a credential sidecar."""

from docker.client import DockerClient
from docker.errors import DockerException
from docker.models.containers import Container

from aicage.docker.errors import DockerError
from aicage.docker.execution.client import get_docker_client

from ._resource_lifecycle import _find_container
from ._resource_models import _CredentialResource
from ._resource_ssh import (
    _close_exec_stream,
    _wait_for_exec_completion,
    _write_exec_input,
)


def _gpg_key_is_protected(resource: _CredentialResource, fingerprint: str) -> bool:
    """Return whether the sidecar's secret key requires a passphrase."""
    client = get_docker_client()
    container = _sidecar_container(client, resource)
    try:
        created = client.api.exec_create(
            container.id,
            ["credential-agent", "gpg", "protected", fingerprint],
        )
        execution_id = created["Id"]
        output = client.api.exec_start(execution_id)
        result = client.api.exec_inspect(execution_id)
    except (DockerException, KeyError) as exc:
        raise DockerError(
            f"Failed to inspect GnuPG key '{fingerprint}' in the credential sidecar."
        ) from exc
    if result.get("ExitCode") != 0:
        raise DockerError(
            f"Failed to inspect GnuPG key '{fingerprint}' in the credential sidecar."
        )
    return output.decode("utf-8").strip() == "protected"


def _load_gpg_key(
    resource: _CredentialResource, fingerprint: str, passphrase: str
) -> None:
    """Load one secret key through the sidecar's stdin-only image contract."""
    client = get_docker_client()
    container = _sidecar_container(client, resource)
    try:
        created = client.api.exec_create(
            container.id,
            ["credential-agent", "gpg", "load", fingerprint],
            stdin=True,
        )
        execution_id = created["Id"]
        stream = client.api.exec_start(execution_id, socket=True)
        try:
            _write_exec_input(stream, passphrase.encode("utf-8") + b"\n")
        finally:
            _close_exec_stream(stream)
        result = _wait_for_exec_completion(client, execution_id)
    except (DockerException, OSError, KeyError) as exc:
        raise DockerError(
            f"Failed to load GnuPG key '{fingerprint}' into the credential sidecar."
        ) from exc
    if result.get("ExitCode") != 0:
        raise DockerError(
            f"Failed to load GnuPG key '{fingerprint}' into the credential sidecar."
        )


def _sidecar_container(
    client: DockerClient, resource: _CredentialResource
) -> Container:
    container = _find_container(client, resource)
    if container is None:
        raise DockerError(
            f"Credential sidecar '{resource.container_name}' is unavailable."
        )
    return container
