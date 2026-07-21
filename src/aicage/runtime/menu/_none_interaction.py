from collections.abc import Callable

from aicage.config.context import ConfigContext
from aicage.config.run_config_draft import RunConfigDraft
from aicage.docker.reporting import OperationReporter
from aicage.registry.image_selection.interaction import (
    BaseChoiceRequest,
    ExtensionChoiceOption,
    MissingExtensionsRequest,
)
from aicage.registry.image_selection.selection import select_agent_image
from aicage.runtime.docker_args.mount_preferences import apply_mount_preferences
from aicage.runtime.menu._interaction_types import ConfigSelectionResult


class _NoneInteraction:
    def configure_run(
        self,
        draft: RunConfigDraft,
        context: ConfigContext,
        agent: str,
    ) -> ConfigSelectionResult:
        selection = select_agent_image(
            agent,
            context,
            _NonInteractiveSelectionInteraction(),
        )
        draft.apply_selection(selection)
        _persist_docker_args(draft)
        _persist_shares(draft)
        apply_mount_preferences(
            context,
            agent,
            draft.parsed,
            _select_all_mounts,
            _always_confirm,
        )
        return ConfigSelectionResult(
            selection=selection,
            project_docker_args=draft.existing_project_docker_args,
        )

    def confirm_aicage_update(
        self,
        installed_version: str,
        latest_version: str,
    ) -> bool:
        del installed_version, latest_version
        return True

    def confirm_image_update(self, image_ref: str) -> bool:
        del image_ref
        return True

    def execute_image_setup(
        self,
        operation: Callable[[OperationReporter | None], None],
    ) -> None:
        operation(None)


class _NonInteractiveSelectionInteraction:
    def choose_base(self, request: BaseChoiceRequest) -> str:
        return request.default_base

    def choose_extensions(
        self,
        options: list[ExtensionChoiceOption],
    ) -> list[str]:
        del options
        return []

    def choose_image_ref(self, default_ref: str) -> str:
        return default_ref

    def choose_missing_extensions(self, request: MissingExtensionsRequest) -> str:
        del request
        return "exit"


def create_none_interaction() -> _NoneInteraction:
    return _NoneInteraction()


def _persist_docker_args(draft: RunConfigDraft) -> None:
    if draft.parsed is None or not draft.parsed.docker_args:
        return
    existing = draft.agent_cfg.docker_args
    if existing == draft.parsed.docker_args:
        return
    draft.persist_docker_args(True)


def _persist_shares(draft: RunConfigDraft) -> None:
    if draft.parsed is None:
        return
    new_shares = draft.persist_shares(False)
    if not new_shares:
        return
    draft.persist_shares(True)


def _always_confirm(*args: object) -> bool:
    del args
    return True


def _select_all_mounts(
    git_items: list[tuple[str, str]],
    extension_items: list[tuple[str, str]],
) -> list[str]:
    return [item[0] for item in [*git_items, *extension_items]]
