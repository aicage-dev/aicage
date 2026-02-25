from unittest import TestCase, mock

from aicage.constants import DEFAULT_EXTENDED_IMAGE_NAME
from aicage.runtime.prompts.image_ref import prompt_for_image_ref


class PromptImageRefTests(TestCase):
    def test_prompt_for_image_ref_returns_default_on_empty(self) -> None:
        with (
            mock.patch("aicage.runtime.prompts.image_ref.ensure_tty_for_prompt"),
            mock.patch("builtins.input", return_value=""),
        ):
            result = prompt_for_image_ref(f"{DEFAULT_EXTENDED_IMAGE_NAME}:default")
        self.assertEqual(f"{DEFAULT_EXTENDED_IMAGE_NAME}:default", result)

    def test_prompt_for_image_ref_adds_prefix_when_missing_tag(self) -> None:
        with (
            mock.patch("aicage.runtime.prompts.image_ref.ensure_tty_for_prompt"),
            mock.patch("builtins.input", return_value="custom"),
        ):
            result = prompt_for_image_ref(f"{DEFAULT_EXTENDED_IMAGE_NAME}:default")
        self.assertEqual(f"{DEFAULT_EXTENDED_IMAGE_NAME}:custom", result)

    def test_prompt_for_image_ref_accepts_tagged_value(self) -> None:
        with (
            mock.patch("aicage.runtime.prompts.image_ref.ensure_tty_for_prompt"),
            mock.patch("builtins.input", return_value="repo:tag"),
        ):
            result = prompt_for_image_ref(f"{DEFAULT_EXTENDED_IMAGE_NAME}:default")
        self.assertEqual("repo:tag", result)

    def test_prompt_for_image_ref_returns_default_when_assume_yes(self) -> None:
        default_ref = f"{DEFAULT_EXTENDED_IMAGE_NAME}:default"
        with (
            mock.patch("aicage.runtime.prompts.image_ref.assume_yes_enabled", return_value=True),
            mock.patch("aicage.runtime.prompts.image_ref.ensure_tty_for_prompt") as tty_mock,
            mock.patch("builtins.input") as input_mock,
        ):
            result = prompt_for_image_ref(default_ref)
        self.assertEqual(default_ref, result)
        tty_mock.assert_not_called()
        input_mock.assert_not_called()
