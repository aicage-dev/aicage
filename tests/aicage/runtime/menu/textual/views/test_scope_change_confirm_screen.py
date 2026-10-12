from unittest import TestCase, mock

from aicage.runtime.menu.textual.views.scope_change_confirm_screen import (
    ScopeChangeConfirmScreen,
)


class ScopeChangeConfirmScreenTests(TestCase):
    def test_init_uses_scope_label(self) -> None:
        screen = ScopeChangeConfirmScreen("global")

        self.assertEqual("global", screen._scope_label)

    def test_compose_builds_screen(self) -> None:
        screen = ScopeChangeConfirmScreen("global")

        self.assertEqual(1, len(list(screen.compose())))

    def test_on_mount_focuses_replace_button(self) -> None:
        screen = ScopeChangeConfirmScreen("global")
        replace_button = mock.Mock()

        with mock.patch.object(screen, "query_one", return_value=replace_button):
            screen.on_mount()

        replace_button.focus.assert_called_once_with()

    def test_on_button_pressed_dismisses_replacement(self) -> None:
        screen = ScopeChangeConfirmScreen("global")
        event = mock.Mock()
        event.button.id = "replace"

        with mock.patch.object(screen, "dismiss") as dismiss_mock:
            screen.on_button_pressed(event)

        event.stop.assert_called_once_with()
        dismiss_mock.assert_called_once_with(True)

    def test_on_button_pressed_dismisses_cancellation(self) -> None:
        screen = ScopeChangeConfirmScreen("global")
        event = mock.Mock()
        event.button.id = "cancel"

        with mock.patch.object(screen, "dismiss") as dismiss_mock:
            screen.on_button_pressed(event)

        dismiss_mock.assert_called_once_with(None)
