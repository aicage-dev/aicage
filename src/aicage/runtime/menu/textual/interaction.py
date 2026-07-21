from collections.abc import Callable
from copy import deepcopy

from aicage.config.context import ConfigContext
from aicage.config.run_config_draft import RunConfigDraft
from aicage.docker.reporting import OperationReporter
from aicage.registry.image_selection.models import ImageSelection
from aicage.runtime.menu._interaction_types import ConfigSelectionResult
from aicage.runtime.menu.prompts.interaction import SimpleInteraction

from ._config_app import ConfigApp
from ._execution_app import ExecutionApp
from ._image_update_app import ImageUpdateApp

_ImageSetupOperation = Callable[[OperationReporter], None]


class TextualInteraction:
    def configure_run(
        self,
        draft: RunConfigDraft,
        context: ConfigContext,
        agent: str,
    ) -> ConfigSelectionResult:
        del agent
        selection, project_docker_args = _edit_draft_with_textual_app(draft, context)
        return ConfigSelectionResult(
            selection=selection,
            project_docker_args=project_docker_args,
        )

    def confirm_aicage_update(
        self,
        installed_version: str,
        latest_version: str,
    ) -> bool:
        return _confirm_update_aicage(installed_version, latest_version)

    def confirm_image_update(self, image_ref: str) -> bool:
        return _confirm_image_update_with_textual_app(image_ref)

    def execute_image_setup(self, operation: _ImageSetupOperation) -> None:
        _execute_image_setup_with_textual_app(operation)


def _edit_draft_with_textual_app(
    draft: RunConfigDraft,
    context: ConfigContext,
) -> tuple[ImageSelection, str]:
    original_project_cfg = deepcopy(draft.project_cfg)
    original_parsed = deepcopy(draft.parsed)
    draft.prefill_for_overview()
    result = ConfigApp(draft, context).run(inline=True)
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


def _confirm_update_aicage(installed_version: str, latest_version: str) -> bool:
    return SimpleInteraction().confirm_aicage_update(installed_version, latest_version)


def _confirm_image_update_with_textual_app(image_ref: str) -> bool:
    return bool(ImageUpdateApp(image_ref).run(inline=True))


def _execute_image_setup_with_textual_app(operation: _ImageSetupOperation) -> None:
    result = ExecutionApp(operation).run(inline=True)
    if isinstance(result, BaseException):
        raise result
