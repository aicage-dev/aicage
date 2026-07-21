from collections.abc import Callable

from textual import work
from textual.app import App, ComposeResult
from textual.content import Content

from aicage.config.resources import find_packaged_path
from aicage.docker.reporting import OperationReporter

from .services.execution_reporting import ExecutionReporter
from .views.execution_screen import ExecutionScreen

_ImageSetupOperation = Callable[[OperationReporter], None]


class ExecutionApp(App[BaseException | None]):
    CSS_PATH = find_packaged_path("textual/app.tcss")
    ENABLE_COMMAND_PALETTE = False
    INLINE_PADDING = 0

    def __init__(self, operation: _ImageSetupOperation) -> None:
        super().__init__()
        self._operation = operation
        self.title = "aicage"
        self.sub_title = "container setup"

    def compose(self) -> ComposeResult:
        yield ExecutionScreen()

    def format_title(self, title: str, sub_title: str) -> Content:
        if not sub_title:
            return Content.from_markup(f"[b]{title}[/b]")
        return Content.from_markup(f"[b]{title}[/b] [dim]— {sub_title}[/dim]")

    def on_mount(self) -> None:
        self._run_execution()

    @work(thread=True, exclusive=True)
    def _run_execution(self) -> None:
        self._run_execution_impl()

    def _run_execution_impl(self) -> None:
        reporter = ExecutionReporter(self.query_one(ExecutionScreen))
        error: BaseException | None = None
        try:
            self._operation(reporter)
        except BaseException as exc:
            error = exc
        self.call_from_thread(self.exit, error)
