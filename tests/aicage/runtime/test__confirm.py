from unittest import TestCase, mock

from aicage.runtime import _confirm
from aicage.runtime._errors import RuntimeExecutionError


class PromptUpdateAicageTests(TestCase):
    def test_prompt_update_aicage_delegates_to_confirmation_prompt(self) -> None:
        with mock.patch(
            "aicage.runtime._confirm._prompt_yes_no", return_value=True
        ) as prompt_mock:
            confirmed = _confirm.prompt_update_aicage("0.9.4", "0.9.5")

        self.assertTrue(confirmed)
        prompt_mock.assert_called_once_with(
            "A newer version of aicage is available "
            "(installed: 0.9.4, latest: 0.9.5). Update now?",
            default=True,
        )


class PromptYesNoTests(TestCase):
    def test_prompt_yes_no_accepts_default(self) -> None:
        with (
            mock.patch("sys.stdin.isatty", return_value=True),
            mock.patch("builtins.input", return_value=""),
        ):
            self.assertTrue(_confirm._prompt_yes_no("Continue?", default=True))
            self.assertFalse(_confirm._prompt_yes_no("Continue?", default=False))

    def test_prompt_yes_no_parses_response(self) -> None:
        with (
            mock.patch("sys.stdin.isatty", return_value=True),
            mock.patch("builtins.input", return_value="yes"),
        ):
            self.assertTrue(_confirm._prompt_yes_no("Continue?", default=False))

    def test_ensure_tty_rejects_non_tty(self) -> None:
        with mock.patch("sys.stdin.isatty", return_value=False):
            with self.assertRaises(RuntimeExecutionError):
                _confirm._ensure_tty()
