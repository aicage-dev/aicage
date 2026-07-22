from unittest import TestCase, mock

from aicage.runtime.menu.textual.views import _cancelable_screen


class CancelableScreenTests(TestCase):
    def test_action_cancel_dismisses_none(self) -> None:
        screen: _cancelable_screen.CancelableScreen[None] = (
            _cancelable_screen.CancelableScreen()
        )

        with mock.patch.object(screen, "dismiss") as dismiss_mock:
            screen.action_cancel()

        dismiss_mock.assert_called_once_with(None)
