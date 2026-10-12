from typing import Any

from textual.containers import Horizontal, Vertical
from textual.widgets import Button, SelectionList, Static
from textual.widgets.selection_list import Selection

from ..._ids import built_in_identity
from ..._models import BuiltInShareValue, CustomShareValue
from ..._mount_display import (
    git_support_config_label,
    mount_selection_rows,
    overview_mount_list_items,
)
from ..._state import OverviewState
from ._selection_list import _OverviewSelectionList

_GIT_MOUNT_KEYS: tuple[str, ...] = ("gitconfig", "gitroot", "gnupg", "ssh")
_GIT_SUPPORT_BUTTON_PREFIX = "git_mount_"


def share_widgets(
    state: OverviewState,
    include_git_support: bool = False,
) -> list[Horizontal | SelectionList | Vertical]:
    return [
        Horizontal(
            Static("Bind Mounts", id="shares_overview_title"),
            Button("+", id="add_share", variant="default"),
            id="shares_overview_header",
        ),
        *(_git_support_widgets(state) if include_git_support else []),
        _OverviewSelectionList(
            *_share_selection_items(state.built_in_shares, state.custom_shares),
            id="shares_overview_list",
            compact=True,
        ),
    ]


def refresh_shares(
    container: Any,
    state: OverviewState,
    include_git_support: bool = False,
) -> None:
    overview = container.query_one("#shares_overview", Vertical)
    if not state.built_in_shares and not state.custom_shares and not include_git_support:
        overview.display = False
        return
    overview.display = True
    container.query_one("#shares_overview_title", Static).update("Bind Mounts")
    selection_list = container.query_one("#shares_overview_list", SelectionList)
    selection_list.clear_options()
    selection_list.add_options(
        _share_selection_items(state.built_in_shares, state.custom_shares)
    )
    if include_git_support:
        for key in _GIT_MOUNT_KEYS:
            container.query_one(f"#{_git_support_button_id(key)}", Button).label = (
                _git_support_value_label(state.git_support_values.get(key))
            )


def merge_built_in_shares(
    fresh_items: list[BuiltInShareValue],
    current_items: list[BuiltInShareValue],
) -> list[BuiltInShareValue]:
    current_by_identity = {
        built_in_identity(item.source, item.key): item for item in current_items
    }
    return [
        BuiltInShareValue(
            source=item.source,
            key=item.key,
            label=item.label,
            path=item.path,
            persisted=_persisted_value(item, current_by_identity),
            enabled=_enabled_value(item, current_by_identity),
            row_key=item.row_key,
            inherited=item.inherited,
        )
        for item in fresh_items
    ]


def _persisted_value(
    item: BuiltInShareValue,
    current_by_identity: dict[str, BuiltInShareValue],
) -> bool | None:
    current = current_by_identity.get(built_in_identity(item.source, item.key))
    if current is not None and current.persisted is None:
        return None
    return item.persisted


def _enabled_value(
    item: BuiltInShareValue,
    current_by_identity: dict[str, BuiltInShareValue],
) -> bool:
    current = current_by_identity.get(built_in_identity(item.source, item.key))
    return current.enabled if current is not None else item.enabled


def current_custom_shares(state: OverviewState) -> list[CustomShareValue]:
    return list(state.custom_shares)


def is_git_support_button(button_id: str | None) -> bool:
    return button_id is not None and button_id.startswith(_GIT_SUPPORT_BUTTON_PREFIX)


def git_support_key(button_id: str) -> str:
    return button_id.removeprefix(_GIT_SUPPORT_BUTTON_PREFIX)


def next_git_support_value(value: bool | None) -> bool | None:
    if value is None:
        return True
    if value:
        return False
    return None


def _git_support_widgets(state: OverviewState) -> list[Vertical]:
    return [
        Vertical(
            *[
                Horizontal(
                    Button(
                        _git_support_value_label(state.git_support_values.get(key)),
                        id=_git_support_button_id(key),
                        classes="git_support_control",
                    ),
                    Static(
                        git_support_config_label(key), classes="git_support_label"
                    ),
                    classes="git_support_row",
                )
                for key in _GIT_MOUNT_KEYS
            ],
            id="git_support_overview",
        )
    ]


def _git_support_button_id(key: str) -> str:
    return f"{_GIT_SUPPORT_BUTTON_PREFIX}{key}"


def _git_support_value_label(value: bool | None) -> str:
    if value is None:
        return "Auto"
    if value:
        return "On\u00a0\u00a0"
    return "Off\u00a0"


def _share_selection_items(
    built_in_shares: list[BuiltInShareValue],
    custom_shares: list[CustomShareValue],
) -> list[Selection[str] | tuple[str, str, bool]]:
    return mount_selection_rows(
        overview_mount_list_items(built_in_shares, custom_shares)
    )
