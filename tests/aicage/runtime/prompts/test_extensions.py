from unittest import TestCase, mock

from aicage.runtime._errors import RuntimeExecutionError
from aicage.runtime.prompts.extensions import ExtensionOption, prompt_for_extensions


class PromptExtensionsTests(TestCase):
    def test_prompt_for_extensions_returns_empty_for_no_options(self) -> None:
        self.assertEqual([], prompt_for_extensions([]))

    def test_prompt_for_extensions_accepts_numbers_and_names(self) -> None:
        options = [
            ExtensionOption(name="one", description="First"),
            ExtensionOption(name="two", description="Second"),
        ]
        with (
            mock.patch("aicage.runtime.prompts.extensions.ensure_tty_for_prompt"),
            mock.patch("builtins.input", return_value="2,one"),
        ):
            selection = prompt_for_extensions(options)
        self.assertEqual(["one", "two"], selection)

    def test_prompt_for_extensions_returns_prompt_order_for_custom_input_order(self) -> None:
        options = [
            ExtensionOption(name="act", description="Act"),
            ExtensionOption(name="cosign", description="Cosign"),
            ExtensionOption(name="gh", description="GitHub CLI"),
            ExtensionOption(name="regctl", description="regctl"),
        ]
        with (
            mock.patch("aicage.runtime.prompts.extensions.ensure_tty_for_prompt"),
            mock.patch("builtins.input", return_value="4,3,2,1"),
        ):
            selection = prompt_for_extensions(options)
        self.assertEqual(["act", "cosign", "gh", "regctl"], selection)

    def test_prompt_for_extensions_returns_empty_on_blank_input(self) -> None:
        options = [
            ExtensionOption(name="one", description="First"),
            ExtensionOption(name="two", description="Second"),
        ]
        with (
            mock.patch("aicage.runtime.prompts.extensions.ensure_tty_for_prompt"),
            mock.patch("builtins.input", return_value=""),
        ):
            selection = prompt_for_extensions(options)
        self.assertEqual([], selection)

    def test_prompt_for_extensions_rejects_duplicates(self) -> None:
        options = [
            ExtensionOption(name="one", description="First"),
            ExtensionOption(name="two", description="Second"),
        ]
        with (
            mock.patch("aicage.runtime.prompts.extensions.ensure_tty_for_prompt"),
            mock.patch("builtins.input", return_value="1,one"),
        ):
            with self.assertRaises(RuntimeExecutionError):
                prompt_for_extensions(options)

    def test_prompt_for_extensions_rejects_invalid_choice(self) -> None:
        options = [
            ExtensionOption(name="one", description="First"),
            ExtensionOption(name="two", description="Second"),
        ]
        with (
            mock.patch("aicage.runtime.prompts.extensions.ensure_tty_for_prompt"),
            mock.patch("builtins.input", return_value="3"),
        ):
            with self.assertRaises(RuntimeExecutionError):
                prompt_for_extensions(options)

    def test_prompt_for_extensions_rejects_invalid_name(self) -> None:
        options = [
            ExtensionOption(name="one", description="First"),
            ExtensionOption(name="two", description="Second"),
        ]
        with (
            mock.patch("aicage.runtime.prompts.extensions.ensure_tty_for_prompt"),
            mock.patch("builtins.input", return_value="unknown"),
        ):
            with self.assertRaises(RuntimeExecutionError):
                prompt_for_extensions(options)

    def test_prompt_for_extensions_returns_default_when_assume_yes(self) -> None:
        options = [
            ExtensionOption(name="one", description="First"),
            ExtensionOption(name="two", description="Second"),
        ]
        with (
            mock.patch("aicage.runtime.prompts.extensions.assume_yes_enabled", return_value=True),
            mock.patch("aicage.runtime.prompts.extensions.ensure_tty_for_prompt") as tty_mock,
            mock.patch("builtins.input") as input_mock,
        ):
            selection = prompt_for_extensions(options)
        self.assertEqual([], selection)
        tty_mock.assert_not_called()
        input_mock.assert_not_called()
