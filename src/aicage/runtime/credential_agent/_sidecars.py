"""Credential-agent sidecar lifecycle."""

from collections.abc import Callable, Iterable
from pathlib import Path

from ._resource_models import _CredentialProtocol, _CredentialResource, _ImageSpec
from ._resources import ResourceSetup, _ensure_resources


def _ensure_sidecars(
    protocols: Iterable[_CredentialProtocol],
    image: _ImageSpec,
    gpg_home: Path | None = None,
    reconcile: Callable[[list[_CredentialResource]], None] | None = None,
) -> list[_CredentialResource]:
    requested = list(dict.fromkeys(protocols))
    if not requested:
        return []
    return _ensure_resources(
        requested,
        image.image_ref,
        image.image_id,
        image.user,
        ResourceSetup(gpg_home, reconcile),
    )
