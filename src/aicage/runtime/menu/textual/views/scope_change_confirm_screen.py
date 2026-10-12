from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Button, Header, Static

from ._cancelable_screen import CancelableScreen


class ScopeChangeConfirmScreen(CancelableScreen[bool | None]):
    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, scope_label: str) -> None:
        super().__init__()
        self._scope_label = scope_label

    def compose(self) -> ComposeResult:
        yield Container(
            Container(
                Header(show_clock=False, classes="app_header"),
                Static("Replace Existing Configuration", classes="screen_title"),
                Static(
                    f"The existing {self._scope_label} configuration for this agent will be replaced.",
                    classes="screen_hint",
                ),
                Horizontal(
                    Button("Cancel", id="cancel", variant="default"),
                    Button("Replace", id="replace", variant="primary"),
                    classes="screen_actions",
                ),
                classes="confirm_shell",
            ),
            classes="screen_frame",
        )

    def on_mount(self) -> None:
        self.query_one("#replace", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "replace":
            self.dismiss(True)
        elif event.button.id == "cancel":
            self.dismiss(None)
