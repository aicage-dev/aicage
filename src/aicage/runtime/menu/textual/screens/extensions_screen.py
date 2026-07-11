import platform
import shutil
import subprocess
from collections.abc import Sequence

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Checkbox, Header, Static, TextArea

from aicage.config.extensions.loader import ExtensionMetadata

from ._screen_support import CancelableScreen


class ExtensionsScreen(CancelableScreen[list[str] | None]):
    _CLIPBOARD_SETTLE_TIMEOUT_SECONDS = 0.2
    _SAMPLES_CLONE_COMMAND = "git clone https://github.com/aicage/aicage-custom-samples.git $HOME/.aicage-custom"

    BINDINGS = [
        Binding("up", "focus_previous_option", "Previous", show=False),
        Binding("down", "focus_next_option", "Next", show=False),
        Binding("enter", "accept", "OK"),
        *CancelableScreen.BINDINGS,
    ]

    def __init__(self, options: list[ExtensionMetadata], selected: list[str]) -> None:
        super().__init__()
        self._options = options
        self._selected = set(selected)

    def on_mount(self) -> None:
        if not self._options:
            self.query_one("#samples_clone_command", TextArea).focus()
            return
        self._focus_checkbox(0)

    def compose(self) -> ComposeResult:
        yield Container(
            Container(
                Header(show_clock=False, classes="app_header"),
                Static("Choose Extensions", classes="screen_title"),
                Static(self._hint_text(), classes="screen_hint"),
                Vertical(*self._content_widgets(), classes="checkbox_group"),
                Horizontal(*self._action_buttons(), classes="screen_actions"),
                classes="screen_shell",
            ),
            classes="screen_frame",
        )

    def action_accept(self) -> None:
        if not self._options:
            self.action_cancel()
            return
        selected = [
            option.extension_id
            for option in self._options
            if self.query_one(f"#ext-{option.extension_id}", Checkbox).value
        ]
        self.dismiss(selected)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "ok":
            self.action_accept()
        elif event.button.id == "copy_command":
            self._copy_samples_command()
        elif event.button.id == "clear":
            self._clear_checkboxes()
        elif event.button.id == "cancel":
            self.action_cancel()

    def action_focus_previous_option(self) -> None:
        self._move_checkbox_focus(-1)

    def action_focus_next_option(self) -> None:
        self._move_checkbox_focus(1)

    def _checkboxes(self) -> list[Checkbox]:
        return [
            Checkbox(
                f"{option.extension_id}: {option.name} - {option.description}",
                value=option.extension_id in self._selected,
                id=f"ext-{option.extension_id}",
            )
            for option in self._options
        ]

    def _content_widgets(self) -> Sequence[Checkbox | Static | TextArea]:
        if not self._options:
            return [
                Static("No optional extensions available.", classes="screen_subtitle"),
                Static("Get samples with:", classes="screen_path"),
                TextArea(
                    self._SAMPLES_CLONE_COMMAND,
                    language="bash",
                    soft_wrap=False,
                    read_only=True,
                    show_cursor=False,
                    id="samples_clone_command",
                    classes="command_box",
                ),
            ]
        return self._checkboxes()

    def _action_buttons(self) -> list[Button]:
        if not self._options:
            return [
                Button("Copy Command", id="copy_command", variant="warning"),
                Button("Back", id="cancel", variant="primary"),
            ]
        return [
            Button("Cancel", id="cancel", variant="default"),
            Button("Clear", id="clear", variant="warning"),
            Button("OK", id="ok", variant="primary"),
        ]

    def _hint_text(self) -> str:
        if not self._options:
            return "Optional extensions are loaded from $HOME/.aicage-custom."
        return "Toggle the optional extensions to include."

    def _copy_samples_command(self) -> None:
        if self._copy_to_system_clipboard(self._SAMPLES_CLONE_COMMAND):
            return
        self.app.copy_to_clipboard(self._SAMPLES_CLONE_COMMAND)

    @classmethod
    def _copy_to_system_clipboard(cls, text: str) -> bool:
        command = cls._clipboard_command()
        if command is None:
            return False
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            start_new_session=True,
        )
        if process.stdin is None:
            return False
        process.stdin.write(text)
        process.stdin.close()
        try:
            process.wait(timeout=cls._CLIPBOARD_SETTLE_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            return True
        return process.returncode == 0

    @staticmethod
    def _clipboard_command() -> list[str] | None:
        system = platform.system()
        if system == "Darwin":
            return ["pbcopy"] if shutil.which("pbcopy") else None
        if system == "Windows":
            return ["clip"] if shutil.which("clip") else None
        for command in (["wl-copy"], ["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]):
            if shutil.which(command[0]):
                return command
        return None

    def _move_checkbox_focus(self, delta: int) -> None:
        if not self._options:
            return
        current_index = self._focused_checkbox_index()
        next_index = min(max(current_index + delta, 0), len(self._options) - 1)
        self._focus_checkbox(next_index)

    def _clear_checkboxes(self) -> None:
        for option in self._options:
            self.query_one(f"#ext-{option.extension_id}", Checkbox).value = False

    def _focused_checkbox_index(self) -> int:
        focused = self.focused
        if not isinstance(focused, Checkbox):
            return 0
        for index, option in enumerate(self._options):
            if focused.id == f"ext-{option.extension_id}":
                return index
        return 0

    def _focus_checkbox(self, index: int) -> None:
        option = self._options[index]
        self.query_one(f"#ext-{option.extension_id}", Checkbox).focus()
