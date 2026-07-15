from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.content import Content
from textual.screen import Screen

from aicage.config.context import ConfigContext
from aicage.config.extensions.loader import ExtensionMetadata
from aicage.config.overview_selection import resolve_overview_selection
from aicage.config.resources import find_packaged_path
from aicage.config.run_config_draft import RunConfigDraft
from aicage.docker.reporting import OperationReporter
from aicage.registry.image_selection.models import ImageSelection

from ._ids import ROW_BASE, ROW_EXTENSIONS, ROW_EXTRAS
from ._models import CustomShareValue, HostAccessConfirmValues
from ._state import OverviewState
from .overview.view import Overview
from .screens.base_screen import BaseScreen
from .screens.docker_args_screen import DockerArgsScreen
from .screens.execution_screen import ExecutionScreen
from .screens.extensions_screen import ExtensionsScreen
from .screens.host_access_confirm_screen import HostAccessConfirmScreen
from .screens.share_editor_screen import ShareEditorScreen
from .services.base_support import base_metadata_for_draft, ensure_base_default
from .services.custom_share_flow import add_custom_share, update_custom_share
from .services.execution_reporting import ExecutionReporter
from .services.host_access_flow import confirm_and_apply_host_access
from .services.summary import extras_values, shares_values

_ScreenResultT = TypeVar("_ScreenResultT")


@dataclass(frozen=True)
class _OverviewResult:
    selection: ImageSelection
    project_docker_args: str


class OverviewApp(App[_OverviewResult | BaseException | None]):
    CSS_PATH = find_packaged_path("textual/overview/app.tcss")
    ENABLE_COMMAND_PALETTE = False
    INLINE_PADDING = 0

    BINDINGS = [
        Binding("enter", "accept", "OK"),
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+c", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        draft: RunConfigDraft,
        context: ConfigContext,
        setup_needed: Callable[[ImageSelection], bool] | None = None,
        execute_setup: (
            Callable[[ImageSelection, OperationReporter], None] | None
        ) = None,
    ) -> None:
        super().__init__()
        self._draft = draft
        self._config_context = context
        self._setup_needed = setup_needed
        self._execute_setup = execute_setup
        self._running_execution = False
        self._state = OverviewState(
            last_section_id=None,
            built_in_shares=shares_values(
                self._draft, self._config_context
            ).built_in_shares,
            custom_shares=[
                CustomShareValue(share) for share in self._draft.agent_cfg.shares
            ],
            docker_socket_enabled=bool(self._draft.agent_cfg.mounts.docker),
        )
        self.title = "aicage"
        self.sub_title = "container config"

    def compose(self) -> ComposeResult:
        yield Overview(self._draft.agent, self._draft.project_cfg.path, self._state)
        execution_screen = ExecutionScreen()
        execution_screen.display = False
        yield execution_screen

    def format_title(self, title: str, sub_title: str) -> Content:
        if not sub_title:
            return Content.from_markup(f"[b]{title}[/b]")
        return Content.from_markup(f"[b]{title}[/b] [dim]— {sub_title}[/dim]")

    def on_mount(self) -> None:
        ensure_base_default(self._draft, self._config_context)
        self._apply_shell_width()
        self._refresh_sections()
        self._overview().focus_default()

    def action_accept(self) -> None:
        if self._running_execution:
            return
        self._accept()

    def action_cancel(self) -> None:
        self._finish(None)

    @work(exclusive=True)
    async def _accept(self) -> None:
        accepted = await self._confirm_undecided_built_in_shares()
        if not accepted:
            return
        result = _OverviewResult(
            selection=resolve_overview_selection(self._draft, self._config_context),
            project_docker_args=self._draft.agent_cfg.docker_args,
        )
        if (
            self._setup_needed is None
            or self._execute_setup is None
            or not self._setup_needed(result.selection)
        ):
            self._finish(result)
            return
        self._show_execution_screen()
        self._run_execution(result)

    @work(exclusive=True)
    async def _edit_section(self, section_id: str) -> None:
        self._state.last_section_id = section_id
        if section_id == ROW_BASE:
            await self._edit_base()
        elif section_id == ROW_EXTENSIONS:
            await self._edit_extensions()
        elif section_id == ROW_EXTRAS:
            await self._edit_extras()
        self._refresh_sections()

    def on_overview_accept_requested(self, _: Overview.AcceptRequested) -> None:
        self.action_accept()

    def on_overview_cancel_requested(self, _: Overview.CancelRequested) -> None:
        self.action_cancel()

    def on_overview_add_share_requested(self, _: Overview.AddShareRequested) -> None:
        self._add_share()

    def on_overview_edit_section_requested(
        self, message: Overview.EditSectionRequested
    ) -> None:
        self._edit_section(message.section_id)

    def on_overview_edit_custom_share_requested(
        self, message: Overview.EditCustomShareRequested
    ) -> None:
        self._edit_custom_share(message.current_value)

    async def _edit_base(self) -> None:
        selected = await self._push_section_screen(
            BaseScreen(
                base_metadata_for_draft(self._draft, self._config_context),
                self._draft.agent_cfg.base or "",
            )
        )
        if selected is not None and selected != self._draft.agent_cfg.base:
            self._draft.agent_cfg.base = selected
            self._draft.reset_extension_image()

    async def _edit_extensions(self) -> None:
        selected = await self._push_section_screen(
            ExtensionsScreen(
                _extension_options(self._config_context),
                list(self._draft.agent_cfg.extensions),
            )
        )
        if selected is not None and selected != self._draft.agent_cfg.extensions:
            self._draft.agent_cfg.extensions = selected
            self._draft.reset_extension_image()

    async def _edit_extras(self) -> None:
        selected = await self._push_section_screen(
            DockerArgsScreen(extras_values(self._draft))
        )
        if selected is None:
            return
        self._draft.agent_cfg.docker_args = selected.docker_args

    @work(exclusive=True)
    async def _add_share(self) -> None:
        result = await self._push_section_screen(ShareEditorScreen())
        if result is None or result.share is None:
            return
        if not add_custom_share(self._state, self._draft, result.share):
            return
        self._apply_shell_width()
        self._refresh_sections()

    @work(exclusive=True)
    async def _edit_custom_share(self, current_value: str) -> None:
        result = await self._push_section_screen(
            ShareEditorScreen(current_value, allow_remove=True)
        )
        if result is None:
            return
        if not update_custom_share(self._state, self._draft, current_value, result):
            return
        self._apply_shell_width()
        self._refresh_sections()

    async def _push_section_screen(
        self, screen: Screen[_ScreenResultT]
    ) -> _ScreenResultT:
        overview = self._overview()
        overview.hide_shell()
        try:
            return await self.push_screen_wait(screen)
        finally:
            overview.show_shell()
            self._focus_last_section()

    def _finish(self, result: _OverviewResult | None) -> None:
        self.exit(result)

    def _focus_last_section(self) -> None:
        if self._state.last_section_id is None:
            self._overview().focus_default()
            return
        self._overview().focus_section(self._state.last_section_id)

    def _apply_shell_width(self) -> None:
        self._overview().apply_shell_width(self.size.width)

    def _refresh_sections(self) -> None:
        self._overview().refresh_from(self._draft, self._config_context)

    def _build_execution_reporting(self) -> tuple[ExecutionScreen, ExecutionReporter]:
        screen = self._execution_screen()
        return screen, ExecutionReporter(screen)

    def _execution_screen(self) -> ExecutionScreen:
        return self.query_one(ExecutionScreen)

    def _show_execution_screen(self) -> None:
        self._running_execution = True
        self.sub_title = "container setup"
        overview = self._overview()
        execution_screen = self._execution_screen()
        overview.display = False
        execution_screen.display = True
        execution_screen.focus()

    @work(thread=True, exclusive=True)
    def _run_execution(self, result: _OverviewResult) -> None:
        _, reporter = self._build_execution_reporting()
        error: BaseException | None = None
        try:
            if self._execute_setup is None:
                raise RuntimeError("Missing Textual setup executor.")
            self._execute_setup(result.selection, reporter)
        except BaseException as exc:
            error = exc
        self.call_from_thread(self._finish_execution, result, error)

    def _finish_execution(
        self,
        result: _OverviewResult,
        error: BaseException | None,
    ) -> None:
        self._running_execution = False
        if error is not None:
            self.exit(error)
            return
        self._finish(result)

    async def _confirm_undecided_built_in_shares(self) -> bool:
        overview = self._overview()
        self._state.custom_shares = overview.current_custom_shares()
        accepted, self._state.built_in_shares = await confirm_and_apply_host_access(
            self._draft,
            overview.current_built_in_shares(),
            self._state.custom_shares,
            overview.current_docker_socket_enabled(self._draft.agent_cfg.mounts.docker),
            self._confirm_host_access,
        )
        return accepted

    def _overview(self) -> Overview:
        return self.query_one(Overview)

    async def _confirm_host_access(
        self,
        values: HostAccessConfirmValues,
    ) -> HostAccessConfirmValues | None:
        return await self._push_section_screen(
            HostAccessConfirmScreen(
                values.docker_options,
                values.git_support_shares,
                values.extension_shares,
            )
        )


def _extension_options(context: ConfigContext) -> list[ExtensionMetadata]:
    return sorted(context.extensions.values(), key=lambda item: item.extension_id)
