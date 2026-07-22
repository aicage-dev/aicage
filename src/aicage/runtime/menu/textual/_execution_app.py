import os
import signal

from textual import work
from textual.app import ComposeResult

from aicage.runtime.menu._interaction_types import ImageSetupOperation

from ._textual_app import TextualApp
from .services.execution_reporting import ExecutionReporter
from .views.execution_screen import ExecutionScreen


class ExecutionApp(TextualApp[BaseException | None]):
    def __init__(self, operation: ImageSetupOperation) -> None:
        super().__init__("container setup")
        self._operation = operation

    def compose(self) -> ComposeResult:
        yield ExecutionScreen()

    def on_mount(self) -> None:
        self._run_execution()

    def action_cancel(self) -> None:
        try:
            os.killpg(os.getpgrp(), signal.SIGINT)
        except (OSError, PermissionError):
            signal.raise_signal(signal.SIGINT)

    @work(thread=True, exclusive=True)
    def _run_execution(self) -> None:
        reporter = ExecutionReporter(self.query_one(ExecutionScreen))
        error: BaseException | None = None
        try:
            self._operation(reporter)
        except BaseException as exc:
            error = exc
        self.call_from_thread(self.exit, error)
