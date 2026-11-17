"""Credential-sidecar resource definitions."""

import os
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from os import name as _os_name
from pathlib import Path, PurePosixPath

_RESOURCE_LABEL = "org.aicage.resource"
_RESOURCE_VALUE = "credential-agent"
_PROTOCOL_LABEL = "org.aicage.credential-agent.protocol"
_IMAGE_ID_LABEL = "org.aicage.credential-agent.image-id"
_OWNER_LABEL = "org.aicage.credential-agent.owner"


class _CredentialProtocol(StrEnum):
    SSH = "ssh"
    GPG = "gpg"


@dataclass(frozen=True)
class _CredentialResource:
    protocol: _CredentialProtocol
    owner: str
    user: str
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


_RESOURCE_PATHS: dict[
    _CredentialProtocol, tuple[PurePosixPath, PurePosixPath, PurePosixPath]
] = {
    _CredentialProtocol.SSH: (
        PurePosixPath("/run/credential-agent"),
        PurePosixPath("/run/credential-agent/ssh-agent.sock"),
        PurePosixPath("/credential/ssh"),
    ),
    _CredentialProtocol.GPG: (
        PurePosixPath("/run/credential-agent"),
        PurePosixPath("/run/credential-agent/S.gpg-agent"),
        PurePosixPath("/credential/gnupg"),
    ),
}


def _resources(
    protocols: Iterable[_CredentialProtocol], user: str = "0:0"
) -> list[_CredentialResource]:
    owner = _resource_owner()
    return [_resource(protocol, owner, user) for protocol in dict.fromkeys(protocols)]


def _resource(
    protocol: _CredentialProtocol, owner: str, user: str
) -> _CredentialResource:
    socket_directory, socket_path, credential_directory = _RESOURCE_PATHS[protocol]
    prefix = f"aicage-credential-agent-{owner}-{protocol.value}"
    return _CredentialResource(
        protocol,
        owner,
        user,
        prefix,
        f"{prefix}-socket",
        socket_directory,
        socket_path,
        credential_directory,
    )


def _resource_owner() -> str:
    if _os_name != "nt":
        return f"u{os.getuid()}"
    profile = str(Path.home()).casefold().encode("utf-8")
    return f"w{sha256(profile).hexdigest()[:12]}"
