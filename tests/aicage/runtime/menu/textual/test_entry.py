from pathlib import Path
from unittest import TestCase, mock

from aicage.cli_types import ParsedArgs
from aicage.config.project_config import AgentConfig
from aicage.registry.image_selection.models import ImageSelection
from aicage.runtime.menu.textual import entry
from aicage.runtime.menu.textual._app import _OverviewResult

from ._test_support import _build_context, _build_draft


class OverviewEntryTests(TestCase):
    def test_edit_draft_with_textual_app_prefills_and_consumes_cli_values(self) -> None:
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
        app_mock.run.return_value = _OverviewResult(
            selection=ImageSelection(
                image_ref="repo:ubuntu",
                base="ubuntu",
                extensions=[],
                base_image_ref="repo:ubuntu",
            ),
            project_docker_args="--new",
        )

        with mock.patch("aicage.runtime.menu.textual.entry.OverviewApp", return_value=app_mock):
            selection, project_docker_args = entry.edit_draft_with_textual_app(draft, context)

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
        app_mock.run.assert_called_once_with(inline=True)

    def test_edit_draft_with_textual_app_reraises_app_error(self) -> None:
        draft = _build_draft(
            agent_cfg=AgentConfig(base="ubuntu"),
            parsed=ParsedArgs(False, "", "codex", [], False, [], None),
        )
        app_mock = mock.Mock()
        app_mock.run.return_value = RuntimeError("boom")

        with (
            mock.patch("aicage.runtime.menu.textual.entry.OverviewApp", return_value=app_mock),
            self.assertRaises(RuntimeError),
        ):
            entry.edit_draft_with_textual_app(draft, _build_context())

    def test_edit_draft_with_textual_app_raises_keyboard_interrupt_on_cancel(self) -> None:
        draft = _build_draft(
            agent_cfg=AgentConfig(base="ubuntu", docker_args="--existing", shares=["/repo/existing"]),
            parsed=ParsedArgs(False, "--new", "codex", [], True, ["logs"], None),
            project_path=Path("/repo"),
        )

        with mock.patch("aicage.runtime.menu.textual.entry.OverviewApp.run", return_value=None):
            with self.assertRaises(KeyboardInterrupt):
                entry.edit_draft_with_textual_app(draft, _build_context())

        parsed = draft.parsed
        if parsed is None:
            self.fail("Expected parsed args to be available.")
        self.assertEqual("--existing", draft.agent_cfg.docker_args)
        self.assertEqual(["/repo/existing"], draft.agent_cfg.shares)
        self.assertIsNone(draft.agent_cfg.mounts.docker)
        self.assertEqual("--new", parsed.docker_args)
        self.assertTrue(parsed.docker_socket)
        self.assertEqual(["logs"], parsed.shares)
