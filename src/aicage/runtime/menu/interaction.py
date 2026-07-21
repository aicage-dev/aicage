from dataclasses import dataclass
from typing import Protocol

from aicage.config.context import ConfigContext
from aicage.config.run_config import RunConfig
from aicage.config.run_config_draft import RunConfigDraft
from aicage.registry.ensure_image import ensure_image
from aicage.registry.image_selection.models import ImageSelection
from aicage.registry.image_selection.selection import select_agent_image
from aicage.runtime.docker_args.mount_preferences import apply_mount_preferences
from aicage.runtime.menu.prompts.confirm import (
    prompt_mount_git_support,
    prompt_persist_docker_args,
    prompt_persist_docker_socket,
    prompt_persist_shares,
    prompt_update_image,
)
from aicage.runtime.menu.textual.entry import edit_draft_with_textual_app
from aicage.runtime.menu.textual.setup import prepare_image_with_textual_app


@dataclass(frozen=True)
class _ConfigSelectionResult:
    selection: ImageSelection
    project_docker_args: str


class RuntimeInteraction(Protocol):
    def configure_run(
        self,
        draft: RunConfigDraft,
        context: ConfigContext,
        agent: str,
    ) -> _ConfigSelectionResult: ...

    def prepare_image(self, run_config: RunConfig) -> None: ...


class _PromptInteraction:
    def configure_run(
        self,
        draft: RunConfigDraft,
        context: ConfigContext,
        agent: str,
    ) -> _ConfigSelectionResult:
        selection = select_agent_image(agent, context)
        draft.apply_selection(selection)
        _persist_docker_args(draft)
        _persist_shares(draft)
        apply_mount_preferences(
            context,
            agent,
            draft.parsed,
            prompt_mount_git_support,
            prompt_persist_docker_socket,
        )
        return _ConfigSelectionResult(
            selection=selection,
            project_docker_args=draft.existing_project_docker_args,
        )

    def prepare_image(self, run_config: RunConfig) -> None:
        ensure_image(run_config, confirm_update=prompt_update_image)


class _TextualInteraction:
    def configure_run(
        self,
        draft: RunConfigDraft,
        context: ConfigContext,
        agent: str,
    ) -> _ConfigSelectionResult:
        del agent
        selection, project_docker_args = edit_draft_with_textual_app(draft, context)
        return _ConfigSelectionResult(
            selection=selection,
            project_docker_args=project_docker_args,
        )

    def prepare_image(self, run_config: RunConfig) -> None:
        prepare_image_with_textual_app(run_config)


def create_runtime_interaction(menu: str) -> RuntimeInteraction:
    if menu == "textual":
        return _TextualInteraction()
    return _PromptInteraction()


def _persist_docker_args(draft: RunConfigDraft) -> None:
    if draft.parsed is None or not draft.parsed.docker_args:
        return
    existing = draft.agent_cfg.docker_args
    if existing == draft.parsed.docker_args:
        return
    draft.persist_docker_args(
        prompt_persist_docker_args(draft.parsed.docker_args, existing),
    )


def _persist_shares(draft: RunConfigDraft) -> None:
    if draft.parsed is None:
        return
    existing_shares = list(draft.agent_cfg.shares)
    new_shares = draft.persist_shares(False)
    if not new_shares:
        return
    draft.persist_shares(prompt_persist_shares(new_shares, existing_shares))
