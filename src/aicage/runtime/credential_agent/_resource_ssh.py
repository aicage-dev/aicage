"""SSH key loading through a credential sidecar."""

import time
from pathlib import PurePosixPath

from docker.client import DockerClient
from docker.errors import DockerException

from aicage.docker.errors import DockerError
from aicage.docker.execution.client import get_docker_client

from ._resource_lifecycle import _find_container
from ._resource_models import _CredentialResource

_EXEC_COMPLETION_TIMEOUT_SECONDS = 10
_EXEC_COMPLETION_POLL_SECONDS = 0.05


def _load_ssh_key(
    resource: _CredentialResource, key_path: PurePosixPath, passphrase: str
) -> None:
    """Load one key through the sidecar's stdin-only image contract."""
    client = get_docker_client()
    container = _find_container(client, resource)
    if container is None:
        raise DockerError(
            f"Credential sidecar '{resource.container_name}' is unavailable."
        )
    try:
        created = client.api.exec_create(
            container.id,
            ["credential-agent", "ssh", "load", key_path.as_posix()],
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
            f"Failed to load SSH key '{key_path.name}' into the credential sidecar."
        ) from exc
    if result.get("ExitCode") != 0:
        raise DockerError(
            f"Failed to load SSH key '{key_path.name}' into the credential sidecar."
        )


def _write_exec_input(stream: object, content: bytes) -> None:
    for socket in (stream, getattr(stream, "_sock", None)):
        sendall = getattr(socket, "sendall", None)
        if callable(sendall):
            sendall(content)
            return
    write = getattr(stream, "write", None)
    writable = getattr(stream, "writable", None)
    if not callable(write) or (callable(writable) and not writable()):
        raise OSError("Docker exec stream does not support stdin.")
    remaining = content
    while remaining:
        written = write(remaining)
        if written is None:
            return
        if not isinstance(written, int) or written <= 0:
            raise OSError("Docker exec stream rejected stdin.")
        remaining = remaining[written:]


def _close_exec_stream(stream: object) -> None:
    response = getattr(stream, "_response", None)
    response_close = getattr(response, "close", None)
    if callable(response_close):
        response_close()
    close = getattr(stream, "close", None)
    if callable(close):
        close()


def _wait_for_exec_completion(
    client: DockerClient, execution_id: str
) -> dict[str, object]:
    deadline = time.monotonic() + _EXEC_COMPLETION_TIMEOUT_SECONDS
    while True:
        result = client.api.exec_inspect(execution_id)
        if not result.get("Running") and result.get("ExitCode") is not None:
            return result
        if time.monotonic() >= deadline:
            return result
        time.sleep(_EXEC_COMPLETION_POLL_SECONDS)
