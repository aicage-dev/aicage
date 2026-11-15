"""GnuPG key loading through a credential sidecar."""

from docker.client import DockerClient
from docker.errors import DockerException
from docker.models.containers import Container

from aicage.docker.errors import DockerError
from aicage.docker.execution.cli import run_docker_command
from aicage.docker.execution.client import get_docker_client

from ._resource_lifecycle import _find_container
from ._resource_models import _CredentialResource
from ._resource_ssh import (
    _terminal_streams,
)


def _gpg_key_is_protected(resource: _CredentialResource, fingerprint: str) -> bool:
    """Return whether the sidecar's secret key requires a passphrase."""
    client = get_docker_client()
    container = _sidecar_container(client, resource)
    output = _run_gpg_command(
        client,
        container,
        ["credential-agent", "gpg", "protected", fingerprint],
        fingerprint,
    )
    return output.strip() == "protected"


def _gpg_key_is_cached(resource: _CredentialResource, fingerprint: str) -> bool:
    client = get_docker_client()
    container = _sidecar_container(client, resource)
    output = _run_gpg_command(
        client,
        container,
        ["credential-agent", "gpg", "cached", fingerprint],
        fingerprint,
    )
    return output.strip() == "cached"


def _gpg_keygrips(resource: _CredentialResource) -> set[str]:
    client = get_docker_client()
    container = _sidecar_container(client, resource)
    output = _run_gpg_command(
        client,
        container,
        ["credential-agent", "gpg", "keygrips"],
        resource.container_name,
    )
    return set(output.splitlines())


def _reset_gpg_agent(resource: _CredentialResource) -> None:
    client = get_docker_client()
    container = _sidecar_container(client, resource)
    _run_gpg_command(
        client,
        container,
        ["credential-agent", "gpg", "reset"],
        resource.container_name,
    )


def _run_gpg_command(
    client: DockerClient, container: Container, command: list[str], identifier: str
) -> str:
    try:
        created = client.api.exec_create(container.id, command)
        execution_id = created["Id"]
        output = client.api.exec_start(execution_id)
        result = client.api.exec_inspect(execution_id)
    except (DockerException, KeyError) as exc:
        raise DockerError(
            f"Failed to inspect GnuPG key '{identifier}' in the credential sidecar."
        ) from exc
    if result.get("ExitCode") != 0:
        details = output.decode("utf-8", errors="replace").strip()
        if details:
            details = details[:1000]
        raise DockerError(
            f"Failed to inspect GnuPG key '{identifier}' in the credential sidecar."
            + (f"\n{details}" if details else "")
        )
    return output.decode("utf-8")


def _load_gpg_key_interactively(resource: _CredentialResource, fingerprint: str) -> None:
    with _terminal_streams() as (stdin, stdout):
        result = run_docker_command(
            [
                "docker",
                "exec",
                "-it",
                resource.container_name,
                "credential-agent",
                "gpg",
                "load-interactive",
                fingerprint,
            ],
            check=False,
            stdin=stdin,
            stdout=stdout,
            stderr=stdout,
        )
    if result.returncode != 0:
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
