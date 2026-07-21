from collections.abc import Callable
from pathlib import Path

from aicage.docker.reporting import OperationReporter
from aicage.runtime.menu.textual.views.execution_screen import ExecutionScreen


class ExecutionReporter(OperationReporter):
    def __init__(self, screen: ExecutionScreen) -> None:
        self._screen = screen

    def on_phase_started(self, phase: str, message: str, log_path: Path) -> None:
        self._dispatch(self._screen.show_phase_started, phase, message, log_path)

    def on_phase_progress(
        self,
        phase: str,
        status: str,
        current: int | None,
        total: int | None,
    ) -> None:
        self._dispatch(self._screen.show_phase_progress, phase, status, current, total)

    def on_phase_log(self, phase: str, line: str) -> None:
        self._dispatch(self._screen.show_phase_log, phase, line)

    def on_phase_finished(self, phase: str, message: str) -> None:
        self._dispatch(self._screen.show_phase_finished, phase, message)

    def on_phase_failed(self, phase: str, message: str, log_path: Path) -> None:
        self._dispatch(self._screen.show_phase_failed, phase, message, log_path)

    def _dispatch(self, callback: Callable[..., None], *args: object) -> None:
        app = getattr(self._screen, "app", None)
        call_from_thread = getattr(app, "call_from_thread", None)
        if not callable(call_from_thread):
            callback(*args)
            return
        try:
            call_from_thread(callback, *args)
        except RuntimeError:
            callback(*args)
