from typing import Generic, TypeVar

from textual.app import App
from textual.binding import Binding
from textual.content import Content

from aicage.config.resources import find_packaged_path

_ResultT = TypeVar("_ResultT")


class TextualApp(App[_ResultT], Generic[_ResultT]):
    CSS_PATH = find_packaged_path("textual/app.tcss")
    ENABLE_COMMAND_PALETTE = False
    INLINE_PADDING = 0
    BINDINGS = [Binding("ctrl+c", "cancel", "Cancel")]

    def __init__(self, sub_title: str) -> None:
        super().__init__()
        self.title = "aicage"
        self.sub_title = sub_title

    def format_title(self, title: str, sub_title: str) -> Content:
        if not sub_title:
            return Content.from_markup(f"[b]{title}[/b]")
        return Content.from_markup(f"[b]{title}[/b] [dim]— {sub_title}[/dim]")

    def action_cancel(self) -> None:
        self.exit(None)
