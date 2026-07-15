from typing import Generic, TypeVar

from textual.binding import Binding
from textual.screen import Screen

_CANCEL_BINDINGS = [
    Binding("escape", "cancel", "Cancel"),
    Binding("ctrl+c", "cancel", "Cancel"),
]
_ResultT = TypeVar("_ResultT")


class CancelableScreen(Screen[_ResultT], Generic[_ResultT]):
    BINDINGS = _CANCEL_BINDINGS

    def action_cancel(self) -> None:
        self.dismiss(None)
