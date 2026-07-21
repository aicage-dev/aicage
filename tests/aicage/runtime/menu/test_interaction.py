from unittest import TestCase, mock

from aicage.cli_types import ParsedArgs
from aicage.config.project_config import AgentConfig
from aicage.registry.image_selection.interaction import (
    BaseChoiceRequest,
    ExtensionChoiceOption,
    MissingExtensionsRequest,
)
from aicage.runtime.menu import interaction

from .textual._test_support import _build_context, _build_draft


class CreateRuntimeInteractionTests(TestCase):
    def test_create_runtime_interaction_returns_textual_interaction_for_textual_mode(
        self,
    ) -> None:
        resolved = interaction.create_runtime_interaction("textual")

        self.assertEqual("_TextualInteraction", resolved.__class__.__name__)

    def test_create_runtime_interaction_returns_none_interaction_for_none_mode(
        self,
    ) -> None:
        resolved = interaction.create_runtime_interaction("none")

        self.assertEqual("_NoneInteraction", resolved.__class__.__name__)

    def test_create_runtime_interaction_returns_simple_interaction_for_simple_mode(
        self,
    ) -> None:
        resolved = interaction.create_runtime_interaction("simple")

        self.assertEqual("_SimpleInteraction", resolved.__class__.__name__)


class ConfigureRunTests(TestCase):
    def test_configure_run_uses_prompt_flow_for_simple_interaction(self) -> None:
        resolved = interaction.create_runtime_interaction("simple")
        draft = _build_draft(
            AgentConfig(base="ubuntu"),
            ParsedArgs(
                False,
                "--cli",
                "codex",
                [],
                False,
                ["logs"],
                None,
                menu="simple",
            ),
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


class ExecuteImageSetupTests(TestCase):
    def test_execute_image_setup_runs_operation_for_simple_interaction(self) -> None:
        resolved = interaction.create_runtime_interaction("simple")
        operation = mock.Mock()

        resolved.execute_image_setup(operation)

        operation.assert_called_once_with(None)

    def test_execute_image_setup_uses_textual_setup_for_textual_interaction(
        self,
    ) -> None:
        resolved = interaction.create_runtime_interaction("textual")
        operation = mock.Mock()

        with mock.patch(
            "aicage.runtime.menu.interaction.execute_image_setup_with_textual_app"
        ) as prepare_mock:
            resolved.execute_image_setup(operation)

        prepare_mock.assert_called_once_with(operation)


class PromptSelectionInteractionTests(TestCase):
    def test_choose_base(self) -> None:
        request = BaseChoiceRequest(
            agent="codex",
            context=_build_context(),
            agent_metadata=mock.Mock(),
            default_base="ubuntu",
        )

        with mock.patch(
            "aicage.runtime.menu.interaction.prompt_for_base",
            return_value="ubuntu",
        ) as prompt_mock:
            choice = interaction._PromptSelectionInteraction().choose_base(request)

        self.assertEqual("ubuntu", choice)
        prompt_mock.assert_called_once()

    def test_choose_extensions(self) -> None:
        with mock.patch(
            "aicage.runtime.menu.interaction.prompt_for_extensions",
            return_value=["gh"],
        ) as prompt_mock:
            choice = interaction._PromptSelectionInteraction().choose_extensions(
                [ExtensionChoiceOption(name="gh", description="GitHub CLI")]
            )

        self.assertEqual(["gh"], choice)
        prompt_mock.assert_called_once()

    def test_choose_image_ref(self) -> None:
        with mock.patch(
            "aicage.runtime.menu.interaction.prompt_for_image_ref",
            return_value="repo:tag",
        ) as prompt_mock:
            choice = interaction._PromptSelectionInteraction().choose_image_ref(
                "repo:default"
            )

        self.assertEqual("repo:tag", choice)
        prompt_mock.assert_called_once_with("repo:default")

    def test_choose_missing_extensions(self) -> None:
        request = MissingExtensionsRequest(
            agent="codex",
            missing=["gh"],
            stored_image_ref="repo:tag",
            project_config_path=mock.Mock(),
            other_projects=[],
        )

        with mock.patch(
            "aicage.runtime.menu.interaction.prompt_for_missing_extensions",
            return_value="exit",
        ) as prompt_mock:
            choice = interaction._PromptSelectionInteraction().choose_missing_extensions(
                request
            )

        self.assertEqual("exit", choice)
        prompt_mock.assert_called_once()


class RuntimeUpdateInteractionTests(TestCase):
    def test_confirm_aicage_update(self) -> None:
        with mock.patch(
            "aicage.runtime.menu.interaction.prompt_update_aicage",
            return_value=True,
        ) as prompt_mock:
            confirmed = interaction.create_runtime_interaction(
                "simple"
            ).confirm_aicage_update("1.0.0", "1.1.0")

        self.assertTrue(confirmed)
        prompt_mock.assert_called_once_with("1.0.0", "1.1.0")

    def test_confirm_image_update(self) -> None:
        with mock.patch(
            "aicage.runtime.menu.interaction.prompt_update_image",
            return_value=True,
        ) as prompt_mock:
            confirmed = interaction.create_runtime_interaction(
                "simple"
            ).confirm_image_update("repo:tag")

        self.assertTrue(confirmed)
        prompt_mock.assert_called_once_with("repo:tag")
