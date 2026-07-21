from unittest import TestCase, mock

from aicage.runtime.menu.textual.views import image_update_confirm_screen


class ImageUpdateConfirmScreenTests(TestCase):
    def test_compose_builds_screen_widgets(self) -> None:
        screen = image_update_confirm_screen.ImageUpdateConfirmScreen("repo:tag")

        widgets = list(screen.compose())

        self.assertEqual(1, len(widgets))

    def test_on_mount_focuses_pull_button(self) -> None:
        screen = image_update_confirm_screen.ImageUpdateConfirmScreen("repo:tag")
        button = mock.Mock()

        with mock.patch.object(screen, "query_one", return_value=button):
            screen.on_mount()

        button.focus.assert_called_once_with()

    def test_on_button_pressed_dismisses_true_for_pull(self) -> None:
        screen = image_update_confirm_screen.ImageUpdateConfirmScreen("repo:tag")
        event = mock.Mock()
        event.button.id = "pull_newer"

        with mock.patch.object(screen, "dismiss") as dismiss_mock:
            screen.on_button_pressed(event)

        event.stop.assert_called_once_with()
        dismiss_mock.assert_called_once_with(True)

    def test_on_button_pressed_dismisses_false_for_keep_local(self) -> None:
        screen = image_update_confirm_screen.ImageUpdateConfirmScreen("repo:tag")
        event = mock.Mock()
        event.button.id = "keep_local"

        with mock.patch.object(screen, "dismiss") as dismiss_mock:
            screen.on_button_pressed(event)

        event.stop.assert_called_once_with()
        dismiss_mock.assert_called_once_with(False)
