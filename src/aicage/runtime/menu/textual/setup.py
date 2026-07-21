from collections.abc import Callable
from typing import TypeAlias

from textual import work
from textual.app import App, ComposeResult

from aicage.config.resources import find_packaged_path
from aicage.config.run_config import RunConfig
from aicage.registry.ensure_image import (
    ImageSetupPlan,
    ensure_image,
    image_setup_needed,
    image_setup_plan,
)

from .screens.execution_screen import ExecutionScreen
from .screens.image_update_confirm_screen import ImageUpdateConfirmScreen
from .services.execution_reporting import ExecutionReporter

_ConfirmImageUpdate: TypeAlias = Callable[[str], bool]


def prepare_image_with_textual_app(run_config: RunConfig) -> None:
    result = _SetupApp(run_config).run(inline=True)
    if isinstance(result, BaseException):
        raise result


class _SetupApp(App[BaseException | None]):
    CSS_PATH = find_packaged_path("textual/overview/app.tcss")
    ENABLE_COMMAND_PALETTE = False
    INLINE_PADDING = 0

    def __init__(self, run_config: RunConfig) -> None:
        super().__init__()
        self._run_config = run_config
        self.title = "aicage"
        self.sub_title = "container setup"

    def compose(self) -> ComposeResult:
        yield ExecutionScreen()

    def on_mount(self) -> None:
        self._prepare()

    @work(exclusive=True)
    async def _prepare(self) -> None:
        plan = image_setup_plan(self._run_config)
        confirm_update = await self._confirm_image_update(plan)
        if not image_setup_needed(self._run_config, confirm_update):
            self.exit(None)
            return
        self._run_execution(confirm_update)

    @work(thread=True, exclusive=True)
    def _run_execution(self, confirm_update: _ConfirmImageUpdate) -> None:
        reporter = ExecutionReporter(self.query_one(ExecutionScreen))
        error: BaseException | None = None
        try:
            ensure_image(
                self._run_config,
                reporter=reporter,
                confirm_update=confirm_update,
            )
        except BaseException as exc:
            error = exc
        self.call_from_thread(self.exit, error)

    async def _confirm_image_update(
        self,
        setup_plan: ImageSetupPlan,
    ) -> _ConfirmImageUpdate:
        if setup_plan.confirm_update_image_ref is None:
            return _keep_local_image
        should_update = await self.push_screen_wait(
            ImageUpdateConfirmScreen(setup_plan.confirm_update_image_ref)
        )
        return _confirm_image_update_choice(
            setup_plan.confirm_update_image_ref,
            bool(should_update),
        )


def _keep_local_image(_: str) -> bool:
    return False


def _confirm_image_update_choice(
    image_ref: str,
    should_update: bool,
) -> _ConfirmImageUpdate:
    def _confirm(candidate_image_ref: str) -> bool:
        if candidate_image_ref != image_ref:
            raise RuntimeError(
                f"Unexpected image update request for '{candidate_image_ref}'."
            )
        return should_update

    return _confirm
