"""GnuPG key loading through a credential sidecar."""

from pathlib import PurePosixPath

from docker.client import DockerClient
from docker.errors import DockerException
from docker.models.containers import Container

from aicage.docker.errors import DockerError
from aicage.docker.execution.client import get_docker_client

from ._resource_lifecycle import _credential_mount_path, _find_container
from ._resource_models import _CredentialResource
from ._resource_ssh import (
    _close_exec_stream,
    _wait_for_exec_completion,
    _write_exec_input,
)

_GPG_AGENT_HOME = (PurePosixPath("/") / "tmp" / "credential-agent").as_posix()
_GPG_FINGERPRINT_FIELD = 9


def _gpg_key_is_protected(resource: _CredentialResource, fingerprint: str) -> bool:
    """Return whether the sidecar's secret key requires a passphrase."""
    client = get_docker_client()
    container = _sidecar_container(client, resource)
    try:
        output = _run_gpg_command(
            client,
            container,
            ["credential-agent", "gpg", "protected", fingerprint],
            fingerprint,
        )
    except DockerError as exc:
        credential_path = _credential_mount_path(container, resource)
        raise DockerError(
            f"{exc}\nCredential home mount: {credential_path}"
        ) from exc
    return output.strip() == "protected"


def _gpg_secret_key_fingerprints(
    resource: _CredentialResource, signing_key: str | None
) -> list[str]:
    """Return the first primary secret-key fingerprint from the sidecar."""
    command = [
        "gpg",
        "--batch",
        "--with-colons",
        "--homedir",
        _GPG_AGENT_HOME,
        "--list-secret-keys",
    ]
    if signing_key and signing_key.strip():
        command.append(signing_key.strip())
    client = get_docker_client()
    container = _sidecar_container(client, resource)
    output = _run_gpg_command(client, container, command, signing_key or "secret keys")
    return _primary_gpg_fingerprints(output)


def _gpg_keygrips(
    client: DockerClient, container: Container, fingerprint: str
) -> list[str]:
    output = _run_gpg_command(
        client,
        container,
        [
            "gpg",
            "--batch",
            "--with-colons",
            "--with-keygrip",
            "--homedir",
            _GPG_AGENT_HOME,
            "--list-keys",
        ],
        fingerprint,
    )
    keygrips: list[str] = []
    primary_fingerprint_pending = False
    selected_primary_key = False
    for line in output.splitlines():
        fields = line.split(":")
        record_type = fields[0]
        if record_type == "pub":
            primary_fingerprint_pending = True
            selected_primary_key = False
        elif record_type == "fpr" and primary_fingerprint_pending:
            selected_primary_key = (
                len(fields) > _GPG_FINGERPRINT_FIELD
                and fields[_GPG_FINGERPRINT_FIELD] == fingerprint
            )
            primary_fingerprint_pending = False
        elif (
            record_type == "grp"
            and selected_primary_key
            and len(fields) > _GPG_FINGERPRINT_FIELD
        ):
            keygrips.append(fields[_GPG_FINGERPRINT_FIELD])
    return keygrips


def _primary_gpg_fingerprints(output: str) -> list[str]:
    fingerprints: list[str] = []
    secret_key_pending = False
    for line in output.splitlines():
        fields = line.split(":")
        record_type = fields[0]
        if record_type == "sec":
            secret_key_pending = True
            continue
        if (
            record_type == "fpr"
            and secret_key_pending
            and len(fields) > _GPG_FINGERPRINT_FIELD
        ):
            fingerprints.append(fields[_GPG_FINGERPRINT_FIELD])
            secret_key_pending = False
            continue
        if record_type in {"sec", "ssb"}:
            secret_key_pending = False
    return fingerprints[:1]


def _gpg_key_info(
    client: DockerClient, container: Container, keygrip: str
) -> str:
    return _run_gpg_command(
        client,
        container,
        [
            "gpg-connect-agent",
            "--raw-socket",
            f"{_GPG_AGENT_HOME}/S.gpg-agent",
            f"KEYINFO {keygrip}",
            "/bye",
        ],
        keygrip,
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
