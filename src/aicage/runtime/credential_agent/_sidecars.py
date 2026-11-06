"""Credential-agent sidecar lifecycle."""

from collections.abc import Iterable
from pathlib import Path

from aicage.registry.credential_image import ensure_credential_image
from aicage.reporting import OperationReporter

from ._resources import _CredentialProtocol, _CredentialResource, _ensure_resources


def _ensure_sidecars(
    protocols: Iterable[_CredentialProtocol],
    user: str,
    reporter: OperationReporter,
    credential_paths: dict[_CredentialProtocol, Path] | None = None,
) -> list[_CredentialResource]:
    requested = list(dict.fromkeys(protocols))
    if not requested:
        return []
    image_ref, image_id = ensure_credential_image(reporter)
    if credential_paths is None:
        return _ensure_resources(requested, image_ref, image_id, user)
    return _ensure_resources(requested, image_ref, image_id, user, credential_paths)
