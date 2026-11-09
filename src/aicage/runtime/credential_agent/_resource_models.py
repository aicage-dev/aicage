"""Credential-sidecar resource definitions."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath

_RESOURCE_LABEL = "org.aicage.resource"
_RESOURCE_VALUE = "credential-agent"
_PROTOCOL_LABEL = "org.aicage.credential-agent.protocol"
_VERSION_LABEL = "org.aicage.credential-agent.version"
_IMAGE_ID_LABEL = "org.aicage.credential-agent.image-id"
_RESOURCE_VERSION = "1"


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
    credential_directory: PurePosixPath


@dataclass(frozen=True)
class _ImageSpec:
    image_ref: str
    image_id: str
    user: str


_RESOURCES: dict[_CredentialProtocol, _CredentialResource] = {
    _CredentialProtocol.SSH: _CredentialResource(
        protocol=_CredentialProtocol.SSH,
        container_name="aicage-credential-agent-ssh",
        volume_name="aicage-credential-agent-ssh-socket",
        socket_directory=PurePosixPath("/run/credential-agent"),
        socket_path=PurePosixPath("/run/credential-agent/ssh-agent.sock"),
        credential_directory=PurePosixPath("/credential/ssh"),
    ),
    _CredentialProtocol.GPG: _CredentialResource(
        protocol=_CredentialProtocol.GPG,
        container_name="aicage-credential-agent-gpg",
        volume_name="aicage-credential-agent-gpg-socket",
        socket_directory=PurePosixPath("/run/credential-agent"),
        socket_path=PurePosixPath("/run/credential-agent/S.gpg-agent"),
        credential_directory=PurePosixPath("/credential/gnupg"),
    ),
}


def _resources(protocols: Iterable[_CredentialProtocol]) -> list[_CredentialResource]:
    return [_RESOURCES[protocol] for protocol in dict.fromkeys(protocols)]
