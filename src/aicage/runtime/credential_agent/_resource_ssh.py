"""SSH key loading through a credential sidecar."""

from pathlib import PurePosixPath

from docker.errors import DockerException

from aicage.docker.errors import DockerError
from aicage.docker.execution.cli import run_docker_command
from aicage.docker.execution.client import get_docker_client

from ._resource_exec import (
    close_exec_stream,
    terminal_streams,
    wait_for_exec_completion,
    write_exec_input,
)
from ._resource_lifecycle import _find_container
from ._resource_models import _CredentialResource


def _load_ssh_key(
    resource: _CredentialResource,
    key_path: PurePosixPath,
    passphrase: str,
    target_path: PurePosixPath | None = None,
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
            [
                "credential-agent",
                "ssh",
                "load",
                key_path.as_posix(),
                (target_path or key_path).as_posix(),
            ],
            stdin=True,
            user=resource.user,
        )
        execution_id = created["Id"]
        stream = client.api.exec_start(execution_id, socket=True)
        try:
            write_exec_input(stream, passphrase.encode("utf-8") + b"\n")
        finally:
            close_exec_stream(stream)
        result = wait_for_exec_completion(client, execution_id)
    except (DockerException, OSError, KeyError) as exc:
        raise DockerError(
            f"Failed to load SSH key '{key_path.name}' into the credential sidecar."
        ) from exc
    if result.get("ExitCode") != 0:
        raise DockerError(
            f"Failed to load SSH key '{key_path.name}' into the credential sidecar."
        )


def _load_ssh_key_interactively(
    resource: _CredentialResource,
    key_path: PurePosixPath,
    target_path: PurePosixPath | None = None,
) -> None:
    with terminal_streams() as (stdin, stdout):
        result = run_docker_command(
            [
                "docker",
                "exec",
                "--user",
                resource.user,
                "-it",
                resource.container_name,
                "credential-agent",
                "ssh",
                "load-interactive",
                key_path.as_posix(),
                (target_path or key_path).as_posix(),
            ],
            check=False,
            stdin=stdin,
            stdout=stdout,
            stderr=stdout,
        )
    if result.returncode != 0:
        raise DockerError(
            f"Failed to load SSH key '{key_path.name}' into the credential sidecar."
        )


def _list_ssh_identities(resource: _CredentialResource) -> list[str]:
    client = get_docker_client()
    container = _find_container(client, resource)
    if container is None:
        raise DockerError(
            f"Credential sidecar '{resource.container_name}' is unavailable."
        )
    try:
        created = client.api.exec_create(
            container.id,
            ["credential-agent", "ssh", "list"],
            user=resource.user,
        )
        execution_id = created["Id"]
        output = client.api.exec_start(execution_id)
        result = wait_for_exec_completion(client, execution_id)
    except (DockerException, KeyError) as exc:
        raise DockerError(
            f"Failed to list SSH identities in credential sidecar '{resource.container_name}'."
        ) from exc
    if result.get("ExitCode") != 0:
        raise DockerError(
            f"Failed to list SSH identities in credential sidecar '{resource.container_name}'."
        )
    return [line for line in output.decode("utf-8").splitlines() if line]


def _remove_ssh_identity(resource: _CredentialResource, identity: str) -> None:
    client = get_docker_client()
    container = _find_container(client, resource)
    if container is None:
        raise DockerError(
            f"Credential sidecar '{resource.container_name}' is unavailable."
        )
    try:
        created = client.api.exec_create(
            container.id,
            ["credential-agent", "ssh", "remove"],
            stdin=True,
            user=resource.user,
        )
        execution_id = created["Id"]
        stream = client.api.exec_start(execution_id, socket=True)
        try:
            write_exec_input(stream, identity.encode("utf-8") + b"\n")
        finally:
            close_exec_stream(stream)
        result = wait_for_exec_completion(client, execution_id)
    except (DockerException, OSError, KeyError) as exc:
        raise DockerError(
            f"Failed to remove an SSH identity from credential sidecar '{resource.container_name}'."
        ) from exc
    if result.get("ExitCode") != 0:
        raise DockerError(
            f"Failed to remove an SSH identity from credential sidecar '{resource.container_name}'."
        )
