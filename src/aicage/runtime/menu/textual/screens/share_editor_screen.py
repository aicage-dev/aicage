from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Checkbox, DirectoryTree, Header, Input, Static

from .._models import ShareEditorResult
from .._mount_value import compose_mount_value, split_mount_value
from ._screen_support import CancelableScreen


class ShareEditorScreen(CancelableScreen[ShareEditorResult | None]):
    BINDINGS = [Binding("enter", "accept", "OK"), *CancelableScreen.BINDINGS]

    def __init__(self, share: str = "", allow_remove: bool = False) -> None:
        super().__init__()
        self._share = share
        self._allow_remove = allow_remove
        self._path_value, self._read_only = split_mount_value(share)

    def compose(self) -> ComposeResult:
        yield Container(
            Container(
                Header(show_clock=False, classes="app_header"),
                Static(
                    "Edit Bind Mount" if self._allow_remove else "Add Bind Mount",
                    classes="screen_title",
                ),
                Static("Host path", classes="screen_subtitle"),
                Input(
                    value=self._path_value,
                    id="share_input",
                    classes="field bind_mount_input",
                ),
                Horizontal(
                    Checkbox(
                        "Read-only",
                        value=self._read_only,
                        id="read_only_toggle",
                        classes="bind_mount_checkbox",
                    ),
                    classes="bind_mount_checkbox_row",
                ),
                Static("Browse filesystem", classes="screen_subtitle"),
                Vertical(
                    DirectoryTree(
                        Path("/"), id="bind_mount_tree", classes="bind_mount_tree"
                    ),
                    classes="bind_mount_tree_frame",
                ),
                Horizontal(
                    Button("Cancel", id="cancel", variant="default"),
                    *(
                        [Button("Remove", id="remove", variant="error")]
                        if self._allow_remove
                        else []
                    ),
                    Button("OK", id="ok", variant="primary"),
                    classes="screen_actions",
                ),
                classes="screen_shell",
            ),
            classes="screen_frame",
        )

    def on_mount(self) -> None:
        self.query_one("#share_input", Input).focus()

    def action_accept(self) -> None:
        path = self.query_one("#share_input", Input).value.strip()
        if not path:
            self.dismiss(ShareEditorResult(None, False))
            return
        self.dismiss(
            ShareEditorResult(
                compose_mount_value(
                    path, self.query_one("#read_only_toggle", Checkbox).value
                ),
                False,
            )
        )

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        self.query_one("#share_input", Input).value = str(event.path)

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        self.query_one("#share_input", Input).value = str(event.path)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "share_input":
            self.action_accept()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "ok":
            self.action_accept()
        elif event.button.id == "cancel":
            self.action_cancel()
        elif event.button.id == "remove":
            self.dismiss(ShareEditorResult(self._share, True))
