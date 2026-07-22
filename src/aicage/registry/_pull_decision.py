from dataclasses import dataclass
from enum import Enum

from aicage.constants import IMAGE_REGISTRY, IMAGE_REPOSITORY
from aicage.docker.query import get_local_repo_digest
from aicage.docker.types import ImageRefRepository
from aicage.registry.digest.remote_digest import get_remote_digest


class _PullDecisionAction(Enum):
    SKIP = "skip"
    PULL = "pull"
    CONFIRM_PULL = "confirm_pull"


@dataclass(frozen=True)
class _PullDecisionPlan:
    action: _PullDecisionAction


def decide_pull(
    image_ref: str,
    update_approved: bool,
) -> bool:
    plan = pull_decision_plan(image_ref)
    match plan.action:
        case _PullDecisionAction.PULL:
            return True
        case _PullDecisionAction.SKIP:
            return False
        case _PullDecisionAction.CONFIRM_PULL:
            return update_approved


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
        return _PullDecisionPlan(action=_PullDecisionAction.PULL)

    remote_digest = get_remote_digest(image_ref)
    if remote_digest is None:
        return _PullDecisionPlan(action=_PullDecisionAction.SKIP)

    if local_digest == remote_digest:
        return _PullDecisionPlan(action=_PullDecisionAction.SKIP)
    return _PullDecisionPlan(action=_PullDecisionAction.CONFIRM_PULL)
