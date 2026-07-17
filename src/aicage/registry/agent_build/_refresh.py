from collections.abc import Callable
from dataclasses import dataclass

from aicage._logging import get_logger
from aicage.docker.query import get_local_repo_digest_for_repo
from aicage.docker.reporting import OperationReporter
from aicage.registry._errors import RegistryError
from aicage.registry.digest.remote_digest import get_remote_digest
from aicage.runtime.menu.prompts.confirm import prompt_update_image

from ._digest import resolve_base_digest

ConfirmImageUpdate = Callable[[str], bool]


@dataclass(frozen=True)
class BaseRefreshPlan:
    resolved_base_image_ref: str | None
    local_base_image_ref: str | None
    confirm_update_image_ref: str | None = None


def refresh_base_image(
    base_image_ref: str,
    base_repository: str,
    reporter: OperationReporter | None = None,
    confirm_update: ConfirmImageUpdate | None = None,
) -> str:
    logger = get_logger()
    plan = refresh_base_image_plan(base_image_ref, base_repository, reporter=reporter)
    if plan.confirm_update_image_ref is None:
        resolved = _resolved_base_image_ref(plan)
        if resolved is None:
            raise RegistryError(f"Failed to resolve base image for {base_image_ref}.")
        return resolved
    if not (confirm_update or prompt_update_image)(plan.confirm_update_image_ref):
        logger.info("Base image pull not required for %s", base_image_ref)
        local_ref = plan.local_base_image_ref
        if local_ref is None:
            raise RegistryError(f"Missing local base image for {base_image_ref}.")
        return local_ref
    return resolve_base_digest(base_image_ref, base_repository, reporter=reporter)


def refresh_base_image_plan(
    base_image_ref: str,
    base_repository: str,
    reporter: OperationReporter | None = None,
) -> BaseRefreshPlan:
    logger = get_logger()
    local_digest = get_local_repo_digest_for_repo(base_image_ref, base_repository)
    local_ref = _local_base_image_ref(base_repository, local_digest)
    remote_digest = get_remote_digest(base_image_ref)
    if remote_digest is None:
        if local_ref is None:
            raise RegistryError(f"Failed to resolve remote digest for {base_image_ref}.")
        logger.warning("Base image digest check failed; using local base image.")
        return BaseRefreshPlan(
            resolved_base_image_ref=local_ref,
            local_base_image_ref=local_ref,
        )

    digest_ref = f"{base_repository}@{remote_digest}"
    if remote_digest == local_digest:
        return BaseRefreshPlan(
            resolved_base_image_ref=digest_ref,
            local_base_image_ref=local_ref,
        )
    if local_ref is None:
        return BaseRefreshPlan(
            resolved_base_image_ref=digest_ref,
            local_base_image_ref=None,
        )
    return BaseRefreshPlan(
        resolved_base_image_ref=None,
        local_base_image_ref=local_ref,
        confirm_update_image_ref=base_image_ref,
    )


def _resolved_base_image_ref(plan: BaseRefreshPlan) -> str | None:
    if plan.resolved_base_image_ref is not None:
        return plan.resolved_base_image_ref
    return plan.local_base_image_ref


def _local_base_image_ref(base_repository: str, local_digest: str | None) -> str | None:
    if local_digest is None:
        return None
    return f"{base_repository}@{local_digest}"
