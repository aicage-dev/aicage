import json
import subprocess

from aicage._logging import get_logger
from aicage.constants import COSIGN_IDENTITY_REGEXP, COSIGN_IMAGE_REF, COSIGN_OIDC_ISSUER
from aicage.docker.cli import run_docker_command_capture
from aicage.docker.pull import run_pull
from aicage.docker.query import (
    cleanup_old_digest,
    get_local_repo_digest_for_repo,
    local_image_exists,
)
from aicage.registry._errors import RegistryError
from aicage.registry._logs import pull_log_path
from aicage.registry.digest.remote_digest import get_remote_digest

_OFFICIAL_IMAGE_ANNOTATIONS: dict[str, dict[str, str]] = {
    "ghcr.io/aicage/aicage": {
        "org.opencontainers.image.source": "https://github.com/aicage/aicage-image",
        "org.opencontainers.image.title": "aicage",
    },
    "ghcr.io/aicage/aicage-image-base": {
        "org.opencontainers.image.source": "https://github.com/aicage/aicage-image-base",
        "org.opencontainers.image.title": "aicage-image-base",
    },
    "ghcr.io/aicage/aicage-image-util": {
        "org.opencontainers.image.source": "https://github.com/aicage/aicage-image-util",
        "org.opencontainers.image.title": "aicage-image-util",
    },
}


def resolve_verified_digest(image_ref: str) -> str:
    logger = get_logger()
    digest = get_remote_digest(image_ref)
    if digest is None:
        raise RegistryError(f"Failed to resolve remote digest for {image_ref}.")

    digest_ref = _with_digest(image_ref, digest)
    _ensure_cosign_image()
    logger.info("Verifying image signature for %s", digest_ref)
    result = _run_cosign_verify(digest_ref)
    output = _format_cosign_output(result)
    if result.returncode == 0:
        if output:
            logger.info("Image signature verification output for %s:\n%s", digest_ref, output)
        _verify_manifest_annotations(digest_ref)
        logger.info("Image signature verification succeeded for %s", digest_ref)
        return digest_ref
    if output:
        logger.error("Image signature verification output for %s:\n%s", digest_ref, output)
    raise RegistryError(
        "Image signature verification failed for "
        f"{digest_ref}.\nCosign output:\n{output}"
    )


def _with_digest(image_ref: str, digest: str) -> str:
    name = image_ref.split("@", 1)[0]
    if ":" in name and name.rfind(":") > name.rfind("/"):
        name = name[: name.rfind(":")]
    return f"{name}@{digest}"


def _run_cosign_verify(image_ref: str) -> subprocess.CompletedProcess[str]:
    command = [
        "docker",
        "run",
        "--rm",
        COSIGN_IMAGE_REF,
        "verify",
        "--certificate-oidc-issuer",
        COSIGN_OIDC_ISSUER,
        "--certificate-identity-regexp",
        COSIGN_IDENTITY_REGEXP,
        image_ref,
    ]
    return run_docker_command_capture(
        command,
        check=False,
        text=True,
    )


def _verify_manifest_annotations(image_ref: str) -> None:
    expected_annotations = _OFFICIAL_IMAGE_ANNOTATIONS.get(_repository_for_image(image_ref))
    if expected_annotations is None:
        return

    annotations = _manifest_annotations(image_ref)
    for key, expected_value in expected_annotations.items():
        actual_value = annotations.get(key)
        if actual_value != expected_value:
            raise RegistryError(
                f"Image manifest annotation {key} mismatch for {image_ref}: "
                f"expected {expected_value!r}, got {actual_value!r}."
            )


def _manifest_annotations(image_ref: str) -> dict[str, str]:
    result = run_docker_command_capture(
        [
            "docker",
            "buildx",
            "imagetools",
            "inspect",
            "--raw",
            image_ref,
        ],
        check=False,
        text=True,
    )
    if result.returncode != 0:
        output = _format_cosign_output(result)
        raise RegistryError(
            f"Failed to inspect image manifest for {image_ref}.\nDocker output:\n{output}"
        )

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RegistryError(f"Invalid manifest JSON returned for {image_ref}.") from exc

    annotations = payload.get("annotations")
    if not isinstance(annotations, dict):
        raise RegistryError(f"Image manifest for {image_ref} is missing annotations.")

    filtered_annotations: dict[str, str] = {}
    for key, value in annotations.items():
        if isinstance(key, str) and isinstance(value, str):
            filtered_annotations[key] = value
    return filtered_annotations


def _format_cosign_output(result: subprocess.CompletedProcess[str]) -> str:
    parts = [result.stdout.strip(), result.stderr.strip()]
    return "\n".join(part for part in parts if part)


def _ensure_cosign_image() -> None:
    logger = get_logger()
    repository = _repository_for_image(COSIGN_IMAGE_REF)
    local_digest = get_local_repo_digest_for_repo(COSIGN_IMAGE_REF, repository)
    if local_image_exists(COSIGN_IMAGE_REF):
        logger.info("Cosign image already present: %s", COSIGN_IMAGE_REF)
        return
    logger.info("Pulling cosign image %s for signature verification", COSIGN_IMAGE_REF)
    log_path = pull_log_path(COSIGN_IMAGE_REF)
    run_pull(COSIGN_IMAGE_REF, log_path)
    cleanup_old_digest(repository, local_digest, COSIGN_IMAGE_REF)


def _repository_for_image(image_ref: str) -> str:
    name = image_ref.split("@", 1)[0]
    last_colon = name.rfind(":")
    if last_colon > name.rfind("/"):
        return name[:last_colon]
    return name
