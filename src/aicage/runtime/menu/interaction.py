from collections.abc import Callable
from typing import Protocol

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
from aicage.runtime.menu._none_interaction import create_none_interaction
from aicage.runtime.menu.prompts.base import BaseSelectionRequest, prompt_for_base
from aicage.runtime.menu.prompts.confirm import (
    prompt_mount_git_support,
    prompt_persist_docker_args,
    prompt_persist_docker_socket,
    prompt_persist_shares,
    prompt_update_aicage,
    prompt_update_image,
)
from aicage.runtime.menu.prompts.extensions import ExtensionOption, prompt_for_extensions
from aicage.runtime.menu.prompts.image_ref import prompt_for_image_ref
from aicage.runtime.menu.prompts.missing_extensions import (
    prompt_for_missing_extensions,
)
from aicage.runtime.menu.textual.entry import edit_draft_with_textual_app
from aicage.runtime.menu.textual.setup import (
    confirm_image_update_with_textual_app,
    execute_image_setup_with_textual_app,
)

_PersistDockerArgsPrompt = Callable[[str, str | None], bool]
_PersistSharesPrompt = Callable[[list[str], list[str]], bool]
_ImageSetupOperation = Callable[[OperationReporter | None], None]


class RuntimeInteraction(Protocol):
    def configure_run(
        self,
        draft: RunConfigDraft,
        context: ConfigContext,
        agent: str,
    ) -> ConfigSelectionResult: ...

    def confirm_aicage_update(
        self,
        installed_version: str,
        latest_version: str,
    ) -> bool: ...

    def confirm_image_update(self, image_ref: str) -> bool: ...

    def execute_image_setup(self, operation: _ImageSetupOperation) -> None: ...


class _SimpleInteraction:
    def configure_run(
        self,
        draft: RunConfigDraft,
        context: ConfigContext,
        agent: str,
    ) -> ConfigSelectionResult:
        selection = select_agent_image(
            agent,
            context,
            _PromptSelectionInteraction(),
        )
        draft.apply_selection(selection)
        _persist_docker_args(draft, prompt_persist_docker_args)
        _persist_shares(draft, prompt_persist_shares)
        apply_mount_preferences(
            context,
            agent,
            draft.parsed,
            prompt_mount_git_support,
            prompt_persist_docker_socket,
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
        return prompt_update_aicage(installed_version, latest_version)

    def confirm_image_update(self, image_ref: str) -> bool:
        return prompt_update_image(image_ref)

    def execute_image_setup(self, operation: _ImageSetupOperation) -> None:
        operation(None)


class _TextualInteraction:
    def configure_run(
        self,
        draft: RunConfigDraft,
        context: ConfigContext,
        agent: str,
    ) -> ConfigSelectionResult:
        del agent
        selection, project_docker_args = edit_draft_with_textual_app(draft, context)
        return ConfigSelectionResult(
            selection=selection,
            project_docker_args=project_docker_args,
        )

    def confirm_aicage_update(
        self,
        installed_version: str,
        latest_version: str,
    ) -> bool:
        return prompt_update_aicage(installed_version, latest_version)

    def confirm_image_update(self, image_ref: str) -> bool:
        return confirm_image_update_with_textual_app(image_ref)

    def execute_image_setup(self, operation: _ImageSetupOperation) -> None:
        execute_image_setup_with_textual_app(operation)


class _PromptSelectionInteraction:
    def choose_base(self, request: BaseChoiceRequest) -> str:
        return prompt_for_base(
            BaseSelectionRequest(
                agent=request.agent,
                context=request.context,
                agent_metadata=request.agent_metadata,
                default_base=request.default_base,
            )
        )

    def choose_extensions(
        self,
        options: list[ExtensionChoiceOption],
    ) -> list[str]:
        return prompt_for_extensions(
            [
                ExtensionOption(
                    name=option.name,
                    description=option.description,
                )
                for option in options
            ]
        )

    def choose_image_ref(self, default_ref: str) -> str:
        return prompt_for_image_ref(default_ref)

    def choose_missing_extensions(self, request: MissingExtensionsRequest) -> str:
        return prompt_for_missing_extensions(
            agent=request.agent,
            missing=request.missing,
            stored_image_ref=request.stored_image_ref,
            project_config_path=request.project_config_path,
            other_projects=request.other_projects,
        )


def create_runtime_interaction(menu: str) -> RuntimeInteraction:
    if menu == "textual":
        return _TextualInteraction()
    if menu == "none":
        return create_none_interaction()
    return _SimpleInteraction()


def _persist_docker_args(
    draft: RunConfigDraft,
    confirm_persist: _PersistDockerArgsPrompt,
) -> None:
    if draft.parsed is None or not draft.parsed.docker_args:
        return
    existing = draft.agent_cfg.docker_args
    if existing == draft.parsed.docker_args:
        return
    draft.persist_docker_args(
        confirm_persist(draft.parsed.docker_args, existing),
    )


def _persist_shares(
    draft: RunConfigDraft,
    confirm_persist: _PersistSharesPrompt,
) -> None:
    if draft.parsed is None:
        return
    existing_shares = list(draft.agent_cfg.shares)
    new_shares = draft.persist_shares(False)
    if not new_shares:
        return
    draft.persist_shares(confirm_persist(new_shares, existing_shares))
