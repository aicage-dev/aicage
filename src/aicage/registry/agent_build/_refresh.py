from dataclasses import dataclass

from aicage._logging import get_logger
from aicage.docker.query import get_local_repo_digest_for_repo
from aicage.docker.reporting import OperationReporter
from aicage.registry._errors import RegistryError
from aicage.registry.digest.remote_digest import get_remote_digest

from ._digest import resolve_base_digest


@dataclass(frozen=True)
class _BaseRefreshPlan:
    image_ref: str
    needs_confirmation: bool


def refresh_base_image(
    base_image_ref: str,
    base_repository: str,
    update_approved: bool,
    reporter: OperationReporter | None = None,
) -> str:
    logger = get_logger()
    plan = refresh_base_image_plan(base_image_ref, base_repository, reporter=reporter)
    if not plan.needs_confirmation:
        return plan.image_ref
    if not update_approved:
        logger.info("Base image pull not required for %s", base_image_ref)
        return plan.image_ref
    return resolve_base_digest(base_image_ref, base_repository, reporter=reporter)


def refresh_base_image_plan(
    base_image_ref: str,
    base_repository: str,
    reporter: OperationReporter | None = None,
) -> _BaseRefreshPlan:
    logger = get_logger()
    local_digest = get_local_repo_digest_for_repo(base_image_ref, base_repository)
    local_ref = _local_base_image_ref(base_repository, local_digest)
    remote_digest = get_remote_digest(base_image_ref)
    if remote_digest is None:
        if local_ref is None:
            raise RegistryError(f"Failed to resolve remote digest for {base_image_ref}.")
        logger.warning("Base image digest check failed; using local base image.")
        return _BaseRefreshPlan(
            image_ref=local_ref,
            needs_confirmation=False,
        )

    digest_ref = f"{base_repository}@{remote_digest}"
    if remote_digest == local_digest:
        return _BaseRefreshPlan(
            image_ref=digest_ref,
            needs_confirmation=False,
        )
    if local_ref is None:
        return _BaseRefreshPlan(
            image_ref=digest_ref,
            needs_confirmation=False,
        )
    return _BaseRefreshPlan(
        image_ref=local_ref,
        needs_confirmation=True,
    )


def _local_base_image_ref(base_repository: str, local_digest: str | None) -> str | None:
    if local_digest is None:
        return None
    return f"{base_repository}@{local_digest}"
