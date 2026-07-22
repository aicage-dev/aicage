from unittest import TestCase, mock

from textual.widgets._data_table import RowKey

from aicage.config.base.models import BaseMetadata
from aicage.runtime.menu.textual.views import base_screen


class BaseScreenTests(TestCase):
    def test_compose_builds_screen_widgets(self) -> None:
        screen = base_screen.BaseScreen({"ubuntu": _base_metadata()}, "ubuntu")

        widgets = list(screen.compose())

        self.assertEqual(1, len(widgets))

    def test_on_mount_populates_base_table(self) -> None:
        screen = base_screen.BaseScreen({"ubuntu": _base_metadata()}, "ubuntu")
        table = mock.Mock()

        with mock.patch.object(screen, "query_one", return_value=table):
            screen.on_mount()

        self.assertEqual(4, table.add_column.call_count)
        table.add_row.assert_called_once()
        table.move_cursor.assert_called_once_with(row=0, column=0)
        table.focus.assert_called_once()

    def test_action_accept_dismisses_selected_base(self) -> None:
        screen = base_screen.BaseScreen({"ubuntu": _base_metadata()}, "ubuntu")
        table = mock.Mock()
        cell_key = mock.Mock()
        cell_key.row_key = "ubuntu"
        table.cursor_row = 0
        table.coordinate_to_cell_key.return_value = cell_key

        with (
            mock.patch.object(screen, "query_one", return_value=table),
            mock.patch.object(screen, "dismiss") as dismiss_mock,
        ):
            screen.action_accept()

        dismiss_mock.assert_called_once_with("ubuntu")

    def test_action_accept_unwraps_textual_row_key_value(self) -> None:
        screen = base_screen.BaseScreen({"ubuntu": _base_metadata()}, "ubuntu")
        table = mock.Mock()
        cell_key = mock.Mock()
        cell_key.row_key = RowKey("ubuntu")
        table.cursor_row = 0
        table.coordinate_to_cell_key.return_value = cell_key

        with (
            mock.patch.object(screen, "query_one", return_value=table),
            mock.patch.object(screen, "dismiss") as dismiss_mock,
        ):
            screen.action_accept()

        dismiss_mock.assert_called_once_with("ubuntu")

    def test_on_button_pressed_dispatches_ok(self) -> None:
        screen = base_screen.BaseScreen({"ubuntu": _base_metadata()}, "ubuntu")
        event = mock.Mock()
        event.button.id = "ok"

        with mock.patch.object(screen, "action_accept") as accept_mock:
            screen.on_button_pressed(event)

        event.stop.assert_called_once_with()
        accept_mock.assert_called_once()

    def test_on_data_table_row_selected_dispatches_ok(self) -> None:
        screen = base_screen.BaseScreen({"ubuntu": _base_metadata()}, "ubuntu")

        with mock.patch.object(screen, "action_accept") as accept_mock:
            screen.on_data_table_row_selected(mock.Mock())

        accept_mock.assert_called_once_with()


def _base_metadata() -> BaseMetadata:
    return BaseMetadata(
        from_image="ubuntu:latest",
        base_image_distro="Ubuntu",
        base_image_description="Default",
        build_local=False,
        local_definition_dir=mock.Mock(),
        architectures=["amd64", "arm64"],
    )
