"""SSH key loading through a credential sidecar."""

from pathlib import PurePosixPath

from docker.errors import DockerException

from aicage.docker.errors import DockerError
from aicage.docker.execution.client import get_docker_client

from ._resource_lifecycle import _find_container
from ._resource_models import _CredentialResource


def _load_ssh_key(resource: _CredentialResource, key_path: PurePosixPath, passphrase: str) -> None:
    """Load one key through the sidecar's stdin-only image contract."""
    client = get_docker_client()
    container = _find_container(client, resource)
    if container is None:
        raise DockerError(f"Credential sidecar '{resource.container_name}' is unavailable.")
    try:
        created = client.api.exec_create(
            container.id, ["aicage-credential-agent", "ssh", "load", key_path.as_posix()], stdin=True
        )
        execution_id = created["Id"]
        stream = client.api.exec_start(execution_id, socket=True)
        stream.sendall(passphrase.encode("utf-8") + b"\n")  # type: ignore[union-attr]
        stream.close()
        result = client.api.exec_inspect(execution_id)
    except (DockerException, OSError, KeyError) as exc:
        raise DockerError(f"Failed to load SSH key '{key_path.name}' into the credential sidecar.") from exc
    if result.get("ExitCode") != 0:
        raise DockerError(f"Failed to load SSH key '{key_path.name}' into the credential sidecar.")
