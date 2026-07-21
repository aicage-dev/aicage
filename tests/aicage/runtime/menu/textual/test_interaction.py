from pathlib import Path
from unittest import TestCase, mock

from aicage.cli_types import ParsedArgs
from aicage.config.project_config import AgentConfig
from aicage.registry.image_selection.models import ImageSelection
from aicage.runtime.menu.textual import interaction

from ._test_support import _build_context, _build_draft


class ConfigureRunTests(TestCase):
    def test_configure_run(self) -> None:
        resolved = interaction.TextualInteraction()
        draft = _build_draft(
            AgentConfig(base="ubuntu"),
            ParsedArgs(False, "", "codex", [], False, [], None, menu="textual"),
        )
        selection = mock.Mock()
        selection.base = "ubuntu"

        with mock.patch(
            "aicage.runtime.menu.textual.interaction._edit_draft_with_textual_app",
            return_value=(selection, "--project"),
        ) as edit_mock:
            result = resolved.configure_run(draft, _build_context(), "codex")

        edit_mock.assert_called_once_with(draft, mock.ANY)
        self.assertIs(selection, result.selection)
        self.assertEqual("--project", result.project_docker_args)


class ExecuteImageSetupTests(TestCase):
    def test_execute_image_setup(self) -> None:
        resolved = interaction.TextualInteraction()
        operation = mock.Mock()

        with mock.patch(
            "aicage.runtime.menu.textual.interaction._execute_image_setup_with_textual_app"
        ) as execute_mock:
            resolved.execute_image_setup(operation)

        execute_mock.assert_called_once_with(operation)


class TextualInteractionTests(TestCase):
    def test_confirm_image_update(self) -> None:
        with mock.patch(
            "aicage.runtime.menu.textual.interaction._confirm_image_update_with_textual_app",
            return_value=True,
        ) as confirm_mock:
            confirmed = interaction.TextualInteraction().confirm_image_update(
                "repo:tag"
            )

        self.assertTrue(confirmed)
        confirm_mock.assert_called_once_with("repo:tag")

    def test_confirm_aicage_update(self) -> None:
        confirmed = interaction.TextualInteraction().confirm_aicage_update(
            "1.0.0",
            "1.1.0",
        )

        self.assertTrue(confirmed)


class EditDraftWithTextualAppTests(TestCase):
    def test__edit_draft_with_textual_app_prefills_and_consumes_cli_values(
        self,
    ) -> None:
        draft = _build_draft(
            agent_cfg=AgentConfig(base="ubuntu"),
            parsed=ParsedArgs(
                dry_run=False,
                docker_args="--new",
                agent="codex",
                agent_args=[],
                docker_socket=True,
                shares=["logs"],
                config_action=None,
            ),
            project_path=Path("/repo"),
        )
        context = _build_context()
        app_mock = mock.Mock()
        app_mock.run.return_value = mock.Mock(
            selection=ImageSelection(
                image_ref="repo:ubuntu",
                base="ubuntu",
                extensions=[],
                base_image_ref="repo:ubuntu",
            ),
            project_docker_args="--new",
        )

        with mock.patch(
            "aicage.runtime.menu.textual.interaction.OverviewApp.for_config",
            return_value=app_mock,
        ):
            selection, project_docker_args = interaction._edit_draft_with_textual_app(
                draft,
                context,
            )

        parsed = draft.parsed
        if parsed is None:
            self.fail("Expected parsed args to be available.")
        self.assertEqual("repo:ubuntu", selection.image_ref)
        self.assertEqual("--new", project_docker_args)
        self.assertEqual("--new", draft.agent_cfg.docker_args)
        self.assertEqual(["/repo/logs"], draft.agent_cfg.shares)
        self.assertTrue(draft.agent_cfg.mounts.docker)
        self.assertEqual("", parsed.docker_args)
        self.assertEqual([], parsed.shares)
        self.assertFalse(parsed.docker_socket)

    def test__edit_draft_with_textual_app_reraises_app_error(self) -> None:
        draft = _build_draft(
            agent_cfg=AgentConfig(base="ubuntu"),
            parsed=ParsedArgs(False, "", "codex", [], False, [], None),
        )
        app_mock = mock.Mock()
        app_mock.run.return_value = RuntimeError("boom")

        with (
            mock.patch(
                "aicage.runtime.menu.textual.interaction.OverviewApp.for_config",
                return_value=app_mock,
            ),
            self.assertRaises(RuntimeError),
        ):
            interaction._edit_draft_with_textual_app(draft, _build_context())

    def test__edit_draft_with_textual_app_raises_keyboard_interrupt_on_cancel(
        self,
    ) -> None:
        draft = _build_draft(
            agent_cfg=AgentConfig(
                base="ubuntu", docker_args="--existing", shares=["/repo/existing"]
            ),
            parsed=ParsedArgs(False, "--new", "codex", [], True, ["logs"], None),
            project_path=Path("/repo"),
        )
        app_mock = mock.Mock()
        app_mock.run.return_value = None

        with (
            mock.patch(
                "aicage.runtime.menu.textual.interaction.OverviewApp.for_config",
                return_value=app_mock,
            ),
            self.assertRaises(KeyboardInterrupt),
        ):
            interaction._edit_draft_with_textual_app(draft, _build_context())

    def test__confirm_image_update_with_textual_app_returns_false_for_none(self) -> None:
        app_mock = mock.Mock()
        app_mock.run.return_value = None

        with mock.patch(
            "aicage.runtime.menu.textual.interaction.OverviewApp.for_image_update_confirmation",
            return_value=app_mock,
        ):
            self.assertFalse(interaction._confirm_image_update_with_textual_app("repo:tag"))

    def test__execute_image_setup_with_textual_app_raises_app_error(self) -> None:
        operation = mock.Mock()
        app_mock = mock.Mock()
        app_mock.run.return_value = RuntimeError("boom")

        with (
            mock.patch(
                "aicage.runtime.menu.textual.interaction.OverviewApp.for_execution",
                return_value=app_mock,
            ),
            self.assertRaises(RuntimeError),
        ):
            interaction._execute_image_setup_with_textual_app(operation)
