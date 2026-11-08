"""Credential-agent sidecar lifecycle."""

from collections.abc import Callable, Iterable
from pathlib import Path

from aicage.registry.credential_image import ensure_credential_image
from aicage.reporting import OperationReporter

from ._resource_models import _CredentialProtocol, _CredentialResource
from ._resources import ResourceSetup, _ensure_resources


def _ensure_sidecars(
    protocols: Iterable[_CredentialProtocol],
    user: str,
    reporter: OperationReporter,
    gpg_home: Path | None = None,
    reconcile: Callable[[list[_CredentialResource]], None] | None = None,
) -> list[_CredentialResource]:
    requested = list(dict.fromkeys(protocols))
    if not requested:
        return []
    image_ref, image_id = ensure_credential_image(reporter)
    return _ensure_resources(
        requested,
        image_ref,
        image_id,
        user,
        ResourceSetup(gpg_home, reconcile),
    )
