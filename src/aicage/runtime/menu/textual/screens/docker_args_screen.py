from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Button, Header, Label, Static, TextArea

from .._models import ExtrasValues
from ._screen_support import CancelableScreen


class DockerArgsScreen(CancelableScreen[ExtrasValues | None]):
    BINDINGS = [Binding("ctrl+enter", "accept", "OK"), *CancelableScreen.BINDINGS]

    def __init__(self, values: ExtrasValues) -> None:
        super().__init__()
        self._values = values

    def compose(self) -> ComposeResult:
        yield Container(
            Container(
                Header(show_clock=False, classes="app_header"),
                Static("Edit Docker Arguments", classes="screen_title"),
                Static(
                    "Enter raw Docker run arguments.\n"
                    "For example: `-e NAME=value` or `--env NAME=value`.\n"
                    "Line breaks outside quotes are treated as whitespace when the command is built.",
                    classes="screen_hint",
                ),
                Label("Docker arguments"),
                TextArea(
                    self._values.docker_args,
                    id="docker_args",
                    classes="field",
                    soft_wrap=False,
                ),
                Horizontal(
                    Button("Cancel", id="cancel", variant="default"),
                    Button("Clear", id="clear", variant="warning"),
                    Button("OK", id="ok", variant="primary"),
                    classes="screen_actions",
                ),
                classes="screen_shell",
            ),
            classes="screen_frame",
        )

    def action_accept(self) -> None:
        self.dismiss(
            ExtrasValues(
                docker_args=self.query_one("#docker_args", TextArea).text.strip(),
            )
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "ok":
            self.action_accept()
        elif event.button.id == "clear":
            self._clear_docker_args()
        elif event.button.id == "cancel":
            self.action_cancel()

    def _clear_docker_args(self) -> None:
        self.query_one("#docker_args", TextArea).load_text("")
