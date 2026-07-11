from unittest import TestCase

from aicage.runtime.menu.textual._models import BuiltInShareValue, CustomShareValue
from aicage.runtime.menu.textual.overview import _layout


class LayoutTests(TestCase):
    def test_shell_width_returns_fixed_width_value(self) -> None:
        width = _layout.shell_width(
            [BuiltInShareValue("git_support", "ssh", "SSH", "/tmp/.ssh", None, True)],
            [CustomShareValue("/tmp/logs")],
            120,
        )

        self.assertIsInstance(width, int)
        self.assertLessEqual(width, 116)
        self.assertGreaterEqual(width, 92)
