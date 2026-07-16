from collections.abc import Callable
from copy import deepcopy
from typing import TypeAlias

from aicage.config.context import ConfigContext
from aicage.config.run_config_draft import RunConfigDraft
from aicage.docker.reporting import OperationReporter
from aicage.registry.ensure_image import ImageSetupPlan
from aicage.registry.image_selection.models import ImageSelection

from ._app import OverviewApp

_ConfirmImageUpdate: TypeAlias = Callable[[str], bool]


def edit_draft_with_textual_app(
    draft: RunConfigDraft,
    context: ConfigContext,
    setup_plan: Callable[[ImageSelection], ImageSetupPlan] | None = None,
    setup_needed: Callable[[ImageSelection, _ConfirmImageUpdate], bool] | None = None,
    execute_setup: (
        Callable[[ImageSelection, OperationReporter, _ConfirmImageUpdate], None] | None
    ) = None,
) -> tuple[ImageSelection, str]:
    original_project_cfg = deepcopy(draft.project_cfg)
    original_parsed = deepcopy(draft.parsed)
    draft.prefill_for_overview()
    result = OverviewApp(
        draft,
        context,
        setup_plan,
        setup_needed,
        execute_setup,
    ).run(inline=True)
    if result is None:
        draft.project_cfg.path = original_project_cfg.path
        draft.project_cfg.agents = original_project_cfg.agents
        draft.parsed = original_parsed
        raise KeyboardInterrupt
    if isinstance(result, BaseException):
        raise result
    selection = getattr(result, "selection", None)
    project_docker_args = getattr(result, "project_docker_args", None)
    if not isinstance(selection, ImageSelection) or not isinstance(
        project_docker_args, str
    ):
        raise RuntimeError("Unexpected Textual overview result.")
    draft.consume_overview_prefill()
    return selection, project_docker_args
