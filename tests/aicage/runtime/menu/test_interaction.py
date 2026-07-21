from unittest import TestCase, mock

from aicage.cli_types import ParsedArgs
from aicage.config.project_config import AgentConfig
from aicage.runtime.menu import interaction
from aicage.runtime.menu.prompts.confirm import prompt_update_image

from .textual._test_support import _build_context, _build_draft


class CreateRuntimeInteractionTests(TestCase):
    def test_create_runtime_interaction_returns_textual_interaction_for_textual_mode(
        self,
    ) -> None:
        resolved = interaction.create_runtime_interaction("textual")

        self.assertEqual("_TextualInteraction", resolved.__class__.__name__)

    def test_create_runtime_interaction_returns_prompt_interaction_for_non_textual_mode(
        self,
    ) -> None:
        resolved = interaction.create_runtime_interaction("none")

        self.assertEqual("_PromptInteraction", resolved.__class__.__name__)


class ConfigureRunTests(TestCase):
    def test_configure_run_uses_prompt_flow_for_non_textual_interaction(self) -> None:
        resolved = interaction.create_runtime_interaction("none")
        draft = _build_draft(
            AgentConfig(base="ubuntu"),
            ParsedArgs(False, "--cli", "codex", [], False, ["logs"], None, menu="none"),
        )
        selection = mock.Mock()
        selection.base = "ubuntu"

        with (
            mock.patch(
                "aicage.runtime.menu.interaction.select_agent_image",
                return_value=selection,
            ),
            mock.patch(
                "aicage.runtime.menu.interaction.prompt_persist_docker_args",
                return_value=True,
            ),
            mock.patch(
                "aicage.runtime.menu.interaction.prompt_persist_shares",
                return_value=True,
            ),
            mock.patch("aicage.runtime.menu.interaction.apply_mount_preferences"),
        ):
            result = resolved.configure_run(draft, _build_context(), "codex")

        self.assertIs(selection, result.selection)

    def test_configure_run_uses_textual_app_for_textual_interaction(self) -> None:
        resolved = interaction.create_runtime_interaction("textual")
        draft = _build_draft(
            AgentConfig(base="ubuntu"),
            ParsedArgs(False, "", "codex", [], False, [], None, menu="textual"),
        )
        selection = mock.Mock()
        selection.base = "ubuntu"

        with mock.patch(
            "aicage.runtime.menu.interaction.edit_draft_with_textual_app",
            return_value=(selection, "--project"),
        ) as edit_mock:
            result = resolved.configure_run(draft, _build_context(), "codex")

        edit_mock.assert_called_once_with(draft, mock.ANY)
        self.assertIs(selection, result.selection)
        self.assertEqual("--project", result.project_docker_args)


class PrepareImageTests(TestCase):
    def test_prepare_image_uses_ensure_image_for_prompt_interaction(self) -> None:
        resolved = interaction.create_runtime_interaction("none")
        run_config = mock.Mock()

        with mock.patch("aicage.runtime.menu.interaction.ensure_image") as ensure_mock:
            resolved.prepare_image(run_config)

        ensure_mock.assert_called_once_with(
            run_config,
            confirm_update=prompt_update_image,
        )

    def test_prepare_image_uses_textual_setup_for_textual_interaction(self) -> None:
        resolved = interaction.create_runtime_interaction("textual")
        run_config = mock.Mock()

        with mock.patch(
            "aicage.runtime.menu.interaction.prepare_image_with_textual_app"
        ) as prepare_mock:
            resolved.prepare_image(run_config)

        prepare_mock.assert_called_once_with(run_config)
