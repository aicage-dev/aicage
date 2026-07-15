from pathlib import Path
from unittest import TestCase, mock

from aicage.runtime.menu.prompts.missing_extensions import prompt_for_missing_extensions


class PromptMissingExtensionsTests(TestCase):
    def test_prompt_for_missing_extensions_lists_projects(self) -> None:
        other_projects = [("/tmp/one", Path("/tmp/one.yml"))]
        with (
            mock.patch(
                "aicage.runtime.menu.prompts.missing_extensions.ensure_tty_for_prompt"
            ),
            mock.patch("builtins.input", return_value="fresh"),
            mock.patch("builtins.print") as print_mock,
        ):
            result = prompt_for_missing_extensions(
                agent="codex",
                missing=["ext"],
                stored_image_ref="aicage:codex-ubuntu",
                project_config_path=Path("/tmp/project.yml"),
                other_projects=other_projects,
            )
        self.assertEqual("fresh", result)
        self.assertTrue(print_mock.called)

    def test_prompt_for_missing_extensions_no_projects(self) -> None:
        with (
            mock.patch(
                "aicage.runtime.menu.prompts.missing_extensions.ensure_tty_for_prompt"
            ),
            mock.patch("builtins.input", return_value="exit"),
            mock.patch("builtins.print") as print_mock,
        ):
            result = prompt_for_missing_extensions(
                agent="codex",
                missing=["ext"],
                stored_image_ref="",
                project_config_path=Path("/tmp/project.yml"),
                other_projects=[],
            )
        self.assertEqual("exit", result)
        self.assertTrue(print_mock.called)

    def test_prompt_for_missing_extensions_returns_default_when_non_interactive_defaults_enabled(
        self,
    ) -> None:
        with (
            mock.patch(
                "aicage.runtime.menu.prompts.missing_extensions.non_interactive_defaults_enabled",
                return_value=True,
            ),
            mock.patch(
                "aicage.runtime.menu.prompts.missing_extensions.ensure_tty_for_prompt"
            ) as tty_mock,
            mock.patch("builtins.input") as input_mock,
            mock.patch("builtins.print") as print_mock,
        ):
            result = prompt_for_missing_extensions(
                agent="codex",
                missing=["ext"],
                stored_image_ref="",
                project_config_path=Path("/tmp/project.yml"),
                other_projects=[],
            )
        self.assertEqual("exit", result)
        tty_mock.assert_not_called()
        input_mock.assert_not_called()
        print_mock.assert_not_called()
