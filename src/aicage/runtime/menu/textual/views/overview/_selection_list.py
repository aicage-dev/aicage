from textual import events
from textual.widgets import SelectionList


class _OverviewSelectionList(SelectionList):
    def _on_focus(self, event: events.Focus) -> None:
        super()._on_focus(event)
        if self.option_count == 0 or self.highlighted is not None:
            return
        self.highlighted = 0
