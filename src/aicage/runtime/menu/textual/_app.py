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
from .screens.image_update_confirm_screen import ImageUpdateConfirmScreen
from .screens.share_editor_screen import ShareEditorScreen
from .services.base_support import base_metadata_for_draft, ensure_base_default
from .services.custom_share_flow import add_custom_share, update_custom_share
from .services.execution_reporting import ExecutionReporter
from .services.host_access_flow import confirm_and_apply_host_access
from .services.summary import extras_values, shares_values

_ScreenResultT = TypeVar("_ScreenResultT")
_ImageSetupOperation = Callable[[OperationReporter], None]


@dataclass(frozen=True)
class _ConfigResult:
    selection: ImageSelection
    project_docker_args: str


@dataclass(frozen=True)
class _ConfigSession:
    draft: RunConfigDraft
    context: ConfigContext


@dataclass(frozen=True)
class _ImageUpdateSession:
    image_ref: str


@dataclass(frozen=True)
class _ExecutionSession:
    operation: _ImageSetupOperation


class TextualApp(App[_ConfigResult | bool | BaseException | None]):
    CSS_PATH = find_packaged_path("textual/app.tcss")
    ENABLE_COMMAND_PALETTE = False
    INLINE_PADDING = 0

    BINDINGS = [
        Binding("enter", "accept", "OK"),
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+c", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        session: _ConfigSession | _ImageUpdateSession | _ExecutionSession,
    ) -> None:
        super().__init__()
        self._session = session
        self._state = self._initial_state()
        self.title = "aicage"
        self.sub_title = self._sub_title()

    @classmethod
    def for_config(
        cls,
        draft: RunConfigDraft,
        context: ConfigContext,
    ) -> "TextualApp":
        return cls(_ConfigSession(draft, context))

    @classmethod
    def for_image_update_confirmation(cls, image_ref: str) -> "TextualApp":
        return cls(_ImageUpdateSession(image_ref))

    @classmethod
    def for_execution(cls, operation: _ImageSetupOperation) -> "TextualApp":
        return cls(_ExecutionSession(operation))

    def compose(self) -> ComposeResult:
        config_session = self._config_session()
        if config_session is not None:
            yield Overview(
                config_session.draft.agent,
                config_session.draft.project_cfg.path,
                self._state,
            )
            execution_screen = ExecutionScreen()
            execution_screen.display = False
            yield execution_screen
            return
        if self._execution_session() is not None:
            yield ExecutionScreen()

    def format_title(self, title: str, sub_title: str) -> Content:
        if not sub_title:
            return Content.from_markup(f"[b]{title}[/b]")
        return Content.from_markup(f"[b]{title}[/b] [dim]— {sub_title}[/dim]")

    def on_mount(self) -> None:
        config_session = self._config_session()
        if config_session is not None:
            ensure_base_default(config_session.draft, config_session.context)
            self._apply_shell_width()
            self._refresh_sections()
            self._overview().focus_default()
            return
        if self._image_update_session() is not None:
            self._show_image_update_confirmation()
            return
        self._run_execution()

    def action_accept(self) -> None:
        self._accept()

    def action_cancel(self) -> None:
        self._finish(None)

    @work(exclusive=True)
    async def _accept(self) -> None:
        await self._accept_async()

    async def _accept_async(self) -> None:
        config_session = self._require_config_session()
        accepted = await self._confirm_undecided_built_in_shares()
        if not accepted:
            return
        result = _ConfigResult(
            selection=resolve_overview_selection(
                config_session.draft,
                config_session.context,
            ),
            project_docker_args=config_session.draft.agent_cfg.docker_args,
        )
        self._finish(result)

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
        config_session = self._require_config_session()
        selected = await self._push_section_screen(
            BaseScreen(
                base_metadata_for_draft(config_session.draft, config_session.context),
                config_session.draft.agent_cfg.base or "",
            )
        )
        if selected is not None and selected != config_session.draft.agent_cfg.base:
            config_session.draft.agent_cfg.base = selected
            config_session.draft.reset_extension_image()

    async def _edit_extensions(self) -> None:
        config_session = self._require_config_session()
        selected = await self._push_section_screen(
            ExtensionsScreen(
                _extension_options(config_session.context),
                list(config_session.draft.agent_cfg.extensions),
            )
        )
        if (
            selected is not None
            and selected != config_session.draft.agent_cfg.extensions
        ):
            config_session.draft.agent_cfg.extensions = selected
            config_session.draft.reset_extension_image()

    async def _edit_extras(self) -> None:
        config_session = self._require_config_session()
        selected = await self._push_section_screen(
            DockerArgsScreen(extras_values(config_session.draft))
        )
        if selected is None:
            return
        config_session.draft.agent_cfg.docker_args = selected.docker_args

    @work(exclusive=True)
    async def _add_share(self) -> None:
        await self._add_share_async()

    async def _add_share_async(self) -> None:
        config_session = self._require_config_session()
        result = await self._push_section_screen(ShareEditorScreen())
        if result is None or result.share is None:
            return
        if not add_custom_share(self._state, config_session.draft, result.share):
            return
        self._apply_shell_width()
        self._refresh_sections()

    @work(exclusive=True)
    async def _edit_custom_share(self, current_value: str) -> None:
        await self._edit_custom_share_async(current_value)

    async def _edit_custom_share_async(self, current_value: str) -> None:
        config_session = self._require_config_session()
        result = await self._push_section_screen(
            ShareEditorScreen(current_value, allow_remove=True)
        )
        if result is None:
            return
        if not update_custom_share(
            self._state,
            config_session.draft,
            current_value,
            result,
        ):
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

    def _finish(self, result: _ConfigResult | None) -> None:
        self.exit(result)

    def _focus_last_section(self) -> None:
        if self._state.last_section_id is None:
            self._overview().focus_default()
            return
        self._overview().focus_section(self._state.last_section_id)

    def _apply_shell_width(self) -> None:
        self._overview().apply_shell_width(self.size.width)

    def _refresh_sections(self) -> None:
        config_session = self._require_config_session()
        self._overview().refresh_from(config_session.draft, config_session.context)

    async def _confirm_undecided_built_in_shares(self) -> bool:
        overview = self._overview()
        self._state.custom_shares = overview.current_custom_shares()
        accepted, self._state.built_in_shares = await confirm_and_apply_host_access(
            self._require_config_session().draft,
            overview.current_built_in_shares(),
            self._state.custom_shares,
            overview.current_docker_socket_enabled(
                self._require_config_session().draft.agent_cfg.mounts.docker
            ),
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

    @work(exclusive=True)
    async def _show_image_update_confirmation(self) -> None:
        image_update_session = self._require_image_update_session()
        result = await self.push_screen_wait(
            ImageUpdateConfirmScreen(image_update_session.image_ref)
        )
        self.exit(bool(result))

    @work(thread=True, exclusive=True)
    def _run_execution(self) -> None:
        execution_session = self._require_execution_session()
        reporter = ExecutionReporter(self.query_one(ExecutionScreen))
        error: BaseException | None = None
        try:
            execution_session.operation(reporter)
        except BaseException as exc:
            error = exc
        self.call_from_thread(self.exit, error)

    def _sub_title(self) -> str:
        if self._config_session() is not None:
            return "container config"
        return "container setup"

    def _initial_state(self) -> OverviewState:
        config_session = self._config_session()
        if config_session is None:
            return OverviewState(None, [], [], False)
        draft = config_session.draft
        context = config_session.context
        return OverviewState(
            last_section_id=None,
            built_in_shares=shares_values(draft, context).built_in_shares,
            custom_shares=[CustomShareValue(share) for share in draft.agent_cfg.shares],
            docker_socket_enabled=bool(draft.agent_cfg.mounts.docker),
        )

    def _config_session(self) -> _ConfigSession | None:
        if isinstance(self._session, _ConfigSession):
            return self._session
        return None

    def _image_update_session(self) -> _ImageUpdateSession | None:
        if isinstance(self._session, _ImageUpdateSession):
            return self._session
        return None

    def _execution_session(self) -> _ExecutionSession | None:
        if isinstance(self._session, _ExecutionSession):
            return self._session
        return None

    def _require_config_session(self) -> _ConfigSession:
        session = self._config_session()
        if session is None:
            raise RuntimeError("TextualApp is not running in config mode.")
        return session

    def _require_image_update_session(self) -> _ImageUpdateSession:
        session = self._image_update_session()
        if session is None:
            raise RuntimeError("TextualApp is not running in image-update mode.")
        return session

    def _require_execution_session(self) -> _ExecutionSession:
        session = self._execution_session()
        if session is None:
            raise RuntimeError("TextualApp is not running in execution mode.")
        return session

    @property
    def _draft(self) -> RunConfigDraft:
        return self._require_config_session().draft

    @property
    def _config_context(self) -> ConfigContext:
        return self._require_config_session().context


def _extension_options(context: ConfigContext) -> list[ExtensionMetadata]:
    return sorted(context.extensions.values(), key=lambda item: item.extension_id)
