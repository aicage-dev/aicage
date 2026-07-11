from unittest import TestCase, mock

from textual.widgets import Checkbox, Input, Static

from aicage.runtime.menu.textual._models import ShareEditorResult
from aicage.runtime.menu.textual.screens import share_editor_screen


class AddShareScreenTests(TestCase):
    def test_compose_builds_screen_widgets(self) -> None:
        screen = share_editor_screen.ShareEditorScreen()

        with mock.patch.object(share_editor_screen, "DirectoryTree", return_value=Static()):
            widgets = list(screen.compose())

        self.assertEqual(1, len(widgets))

    def test_on_mount_focuses_path_input(self) -> None:
        screen = share_editor_screen.ShareEditorScreen()
        path_input = mock.Mock(spec=Input)

        with mock.patch.object(screen, "query_one", return_value=path_input):
            screen.on_mount()

        path_input.focus.assert_called_once_with()

    def test_action_accept_dismisses_trimmed_bind_mount_with_read_only_suffix(self) -> None:
        screen = share_editor_screen.ShareEditorScreen()
        share_input = mock.Mock()
        share_input.value = "  logs  "
        read_only_toggle = mock.Mock(spec=Checkbox)
        read_only_toggle.value = True

        def query_one_side_effect(selector: str, _expected_type: object) -> mock.Mock:
            if selector == "#share_input":
                return share_input
            if selector == "#read_only_toggle":
                return read_only_toggle
            self.fail(f"Unexpected selector: {selector}")

        with (
            mock.patch.object(screen, "query_one", side_effect=query_one_side_effect),
            mock.patch.object(screen, "dismiss") as dismiss_mock,
        ):
            screen.action_accept()

        dismiss_mock.assert_called_once_with(ShareEditorResult("logs:ro", False))

    def test_action_accept_dismisses_none_for_blank_input(self) -> None:
        screen = share_editor_screen.ShareEditorScreen()
        share_input = mock.Mock()
        share_input.value = "   "

        with (
            mock.patch.object(screen, "query_one", return_value=share_input),
            mock.patch.object(screen, "dismiss") as dismiss_mock,
        ):
            screen.action_accept()

        dismiss_mock.assert_called_once_with(ShareEditorResult(None, False))

    def test_on_directory_tree_directory_selected_updates_input_value(self) -> None:
        screen = share_editor_screen.ShareEditorScreen()
        share_input = mock.Mock(spec=Input)
        event = mock.Mock()
        event.path = "/tmp/logs"

        with mock.patch.object(screen, "query_one", return_value=share_input):
            screen.on_directory_tree_directory_selected(event)

        self.assertEqual("/tmp/logs", share_input.value)

    def test_on_directory_tree_file_selected_updates_input_value(self) -> None:
        screen = share_editor_screen.ShareEditorScreen()
        share_input = mock.Mock(spec=Input)
        event = mock.Mock()
        event.path = "/tmp/config.txt"

        with mock.patch.object(screen, "query_one", return_value=share_input):
            screen.on_directory_tree_file_selected(event)

        self.assertEqual("/tmp/config.txt", share_input.value)

    def test_on_input_submitted_dispatches_accept_for_share_input(self) -> None:
        screen = share_editor_screen.ShareEditorScreen()
        event = mock.Mock()
        event.input.id = "share_input"

        with mock.patch.object(screen, "action_accept") as accept_mock:
            screen.on_input_submitted(event)

        accept_mock.assert_called_once_with()

    def test_on_button_pressed_dispatches_ok(self) -> None:
        screen = share_editor_screen.ShareEditorScreen()
        event = mock.Mock()
        event.button.id = "ok"

        with mock.patch.object(screen, "action_accept") as accept_mock:
            screen.on_button_pressed(event)

        event.stop.assert_called_once_with()
        accept_mock.assert_called_once_with()

    def test_on_button_pressed_dispatches_remove(self) -> None:
        screen = share_editor_screen.ShareEditorScreen("/tmp/project/logs", allow_remove=True)
        event = mock.Mock()
        event.button.id = "remove"

        with mock.patch.object(screen, "dismiss") as dismiss_mock:
            screen.on_button_pressed(event)

        event.stop.assert_called_once_with()
        dismiss_mock.assert_called_once_with(ShareEditorResult("/tmp/project/logs", True))
