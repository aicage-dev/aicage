"""Credential-agent image lifecycle."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from threading import RLock

from aicage.constants import CREDENTIAL_AGENT_IMAGE, IMAGE_REGISTRY
from aicage.docker.errors import DockerError
from aicage.docker.pull import run_pull
from aicage.docker.query import (
    cleanup_old_digest,
    get_local_image_id,
    get_local_repo_digest_for_repo,
)
from aicage.registry._logs import pull_log_path
from aicage.registry._signature import resolve_verified_digest
from aicage.registry.digest.remote_digest import get_remote_digest
from aicage.reporting import OperationReporter

_CREDENTIAL_IMAGE_LOCK = RLock()


@dataclass
class _CredentialImageSession:
    depth: int = 0
    image: tuple[str, str] | None = None


_CREDENTIAL_IMAGE_SESSION = _CredentialImageSession()


@contextmanager
def credential_image_session() -> Iterator[None]:
    """Cache credential-image setup for one Aicage invocation."""
    with _CREDENTIAL_IMAGE_LOCK:
        if _CREDENTIAL_IMAGE_SESSION.depth == 0:
            _CREDENTIAL_IMAGE_SESSION.image = None
        _CREDENTIAL_IMAGE_SESSION.depth += 1
    try:
        yield
    finally:
        with _CREDENTIAL_IMAGE_LOCK:
            _CREDENTIAL_IMAGE_SESSION.depth -= 1
            if _CREDENTIAL_IMAGE_SESSION.depth == 0:
                _CREDENTIAL_IMAGE_SESSION.image = None


def ensure_credential_image(reporter: OperationReporter) -> tuple[str, str]:
    with _CREDENTIAL_IMAGE_LOCK:
        if _CREDENTIAL_IMAGE_SESSION.image is not None:
            return _CREDENTIAL_IMAGE_SESSION.image
        image_ref = CREDENTIAL_AGENT_IMAGE
        repository = _repository(image_ref)
        local_digest = get_local_repo_digest_for_repo(image_ref, repository)
        if local_digest is None:
            _pull(image_ref, repository, local_digest, reporter)
        else:
            remote_digest = get_remote_digest(image_ref)
            if remote_digest is not None and remote_digest != local_digest:
                _pull(image_ref, repository, local_digest, reporter)
        image_id = get_local_image_id(image_ref)
        if image_id is None:
            raise DockerError(
                f"Credential-agent image is unavailable after setup: {image_ref}."
            )
        image = image_ref, image_id
        if _CREDENTIAL_IMAGE_SESSION.depth > 0:
            _CREDENTIAL_IMAGE_SESSION.image = image
        return image


def _pull(
    image_ref: str,
    repository: str,
    local_digest: str | None,
    reporter: OperationReporter,
) -> None:
    log_path = pull_log_path(image_ref)
    resolve_verified_digest(image_ref, reporter=reporter)
    run_pull(image_ref, log_path, reporter=reporter)
    cleanup_old_digest(repository, local_digest, image_ref)


def _repository(image_ref: str) -> str:
    name = image_ref.split("@", 1)[0]
    last_colon = name.rfind(":")
    if last_colon > name.rfind("/"):
        return name[:last_colon]
    return f"{IMAGE_REGISTRY}/{name}"
