from unittest import TestCase, mock

from aicage.runtime.menu.textual.screens import _screen_support as screen_support


class ScreenSupportTests(TestCase):
    def test_action_cancel_dismisses_none(self) -> None:
        screen: screen_support.CancelableScreen[None] = (
            screen_support.CancelableScreen()
        )

        with mock.patch.object(screen, "dismiss") as dismiss_mock:
            screen.action_cancel()

        dismiss_mock.assert_called_once_with(None)
