from unittest import TestCase

from aicage.runtime.prompts import mode


class PromptModeTests(TestCase):
    def test_set_assume_yes(self) -> None:
        mode.set_assume_yes(True)
        self.assertTrue(mode.assume_yes_enabled())
        mode.set_assume_yes(False)

    def test_assume_yes_enabled(self) -> None:
        mode.set_assume_yes(False)
        self.assertFalse(mode.assume_yes_enabled())
