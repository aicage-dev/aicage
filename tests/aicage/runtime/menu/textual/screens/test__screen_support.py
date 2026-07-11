from unittest import TestCase, mock

from aicage.runtime.menu.textual.screens import _screen_support


class ScreenSupportTests(TestCase):
    def test_action_cancel_dismisses_none(self) -> None:
        screen = _screen_support.CancelableScreen()

        with mock.patch.object(screen, "dismiss") as dismiss_mock:
            screen.action_cancel()

        dismiss_mock.assert_called_once_with(None)
