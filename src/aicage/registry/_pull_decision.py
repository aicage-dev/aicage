from collections.abc import Callable
from dataclasses import dataclass

from aicage.constants import IMAGE_REGISTRY, IMAGE_REPOSITORY
from aicage.docker.query import get_local_repo_digest
from aicage.docker.types import ImageRefRepository
from aicage.registry.digest.remote_digest import get_remote_digest

ConfirmImageUpdate = Callable[[str], bool]


@dataclass(frozen=True)
class _PullDecisionPlan:
    should_pull: bool
    confirm_update_image_ref: str | None = None


def _confirm_update_pull(_: str) -> bool:
    return True


def decide_pull(
    image_ref: str,
    confirm_update: ConfirmImageUpdate = _confirm_update_pull,
) -> bool:
    plan = pull_decision_plan(image_ref)
    if plan.confirm_update_image_ref is None:
        return plan.should_pull
    return confirm_update(plan.confirm_update_image_ref)


def pull_decision_plan(image_ref: str) -> _PullDecisionPlan:
    # Local digests include registry prefix; registry API uses repository only.
    local_repository = f"{IMAGE_REGISTRY}/{IMAGE_REPOSITORY}"
    local_digest = get_local_repo_digest(
        ImageRefRepository(
            image_ref=image_ref,
            repository=local_repository,
        )
    )
    if local_digest is None:
        return _PullDecisionPlan(should_pull=True)

    remote_digest = get_remote_digest(image_ref)
    if remote_digest is None:
        return _PullDecisionPlan(should_pull=False)

    if local_digest == remote_digest:
        return _PullDecisionPlan(should_pull=False)
    return _PullDecisionPlan(
        should_pull=False,
        confirm_update_image_ref=image_ref,
    )
