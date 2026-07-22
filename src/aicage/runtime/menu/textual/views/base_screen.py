from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.coordinate import Coordinate
from textual.widgets import Button, DataTable, Header, Static

from aicage.config.base.models import BaseMetadata

from ._screen_support import CancelableScreen

_BASE_COLUMN_KEY = "base"
_DISTRO_COLUMN_KEY = "distro"
_SOURCE_COLUMN_KEY = "source"
_DESCRIPTION_COLUMN_KEY = "description"
_DESCRIPTION_WIDTH = 52


class BaseScreen(CancelableScreen[str | None]):
    BINDINGS = [Binding("enter", "accept", "OK"), *CancelableScreen.BINDINGS]

    def __init__(self, bases: dict[str, BaseMetadata], current_base: str) -> None:
        super().__init__()
        self._bases = bases
        self._current_base = current_base

    def compose(self) -> ComposeResult:
        yield Container(
            Container(
                Header(show_clock=False, classes="app_header"),
                Static("Choose Base", classes="screen_title"),
                Static(
                    "Pick the runtime image used inside the container.",
                    classes="screen_hint",
                ),
                DataTable(id="base_table", classes="base_table"),
                Horizontal(
                    Button("Cancel", id="cancel", variant="default"),
                    Button("OK", id="ok", variant="primary"),
                    classes="screen_actions",
                ),
                classes="screen_shell",
            ),
            classes="screen_frame",
        )

    def on_mount(self) -> None:
        table = self.query_one("#base_table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        table.add_column("base", key=_BASE_COLUMN_KEY)
        table.add_column("distro", key=_DISTRO_COLUMN_KEY)
        table.add_column("source", key=_SOURCE_COLUMN_KEY)
        table.add_column(
            "description", key=_DESCRIPTION_COLUMN_KEY, width=_DESCRIPTION_WIDTH
        )
        selected_index = 0
        for index, (base, metadata) in enumerate(self._bases.items()):
            table.add_row(
                base,
                metadata.base_image_distro,
                _source_summary(metadata),
                _fit_description(metadata.base_image_description),
                key=base,
            )
            if base == self._current_base:
                selected_index = index
        table.move_cursor(row=selected_index, column=0)
        table.focus()

    def action_accept(self) -> None:
        self.dismiss(_selected_base(self.query_one("#base_table", DataTable)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "ok":
            self.action_accept()
        elif event.button.id == "cancel":
            self.action_cancel()

    def on_data_table_row_selected(self, _: DataTable.RowSelected) -> None:
        self.action_accept()


def _selected_base(table: DataTable) -> str:
    cell_key = table.coordinate_to_cell_key(Coordinate(max(table.cursor_row, 0), 0))
    row_key = cell_key.row_key
    if isinstance(row_key, str):
        return row_key
    row_key_value = getattr(row_key, "value", None)
    if isinstance(row_key_value, str):
        return row_key_value
    return str(row_key)


def _source_summary(metadata: BaseMetadata) -> str:
    return "local" if metadata.build_local else "remote"


def _fit_description(description: str) -> str:
    single_line = " ".join(description.split())
    if len(single_line) <= _DESCRIPTION_WIDTH:
        return single_line
    return f"{single_line[: _DESCRIPTION_WIDTH - 1]}..."
