from unittest import TestCase

from aicage.runtime.menu.prompts import mode


class PromptModeTests(TestCase):
    def test_set_non_interactive_defaults(self) -> None:
        mode.set_non_interactive_defaults(True)
        self.assertTrue(mode.non_interactive_defaults_enabled())
        mode.set_non_interactive_defaults(False)

    def test_non_interactive_defaults_enabled(self) -> None:
        mode.set_non_interactive_defaults(False)
        self.assertFalse(mode.non_interactive_defaults_enabled())
