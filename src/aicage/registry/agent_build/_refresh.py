from aicage._logging import get_logger
from aicage.docker.query import get_local_repo_digest_for_repo
from aicage.registry._errors import RegistryError
from aicage.registry._signature import resolve_verified_digest
from aicage.runtime.prompts.confirm import prompt_update_image

from ._digest import resolve_base_digest


def refresh_base_image(
    base_image_ref: str,
    base_repository: str,
) -> str:
    logger = get_logger()
    local_digest = get_local_repo_digest_for_repo(base_image_ref, base_repository)
    try:
        digest_ref = resolve_verified_digest(base_image_ref)
    except RegistryError:
        if not local_digest:
            raise
        logger.warning("Base image digest check failed; using local base image.")
        return f"{base_repository}@{local_digest}"

    remote_digest = digest_ref.split("@", 1)[1]
    if remote_digest == local_digest:
        return digest_ref
    if local_digest and not prompt_update_image(base_image_ref):
        logger.info("Base image pull not required for %s", base_image_ref)
        return f"{base_repository}@{local_digest}"
    return resolve_base_digest(base_image_ref, base_repository)
