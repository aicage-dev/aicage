from typing import Any

from textual.containers import Horizontal, Vertical
from textual.widgets import Button, SelectionList, Static

from ..._ids import built_in_identity
from ..._models import BuiltInShareValue, CustomShareValue
from ..._mount_display import mount_selection_rows, overview_mount_list_items
from ..._state import OverviewState
from ._selection_list import _OverviewSelectionList


def share_widgets(state: OverviewState) -> list[Horizontal | SelectionList]:
    return [
        Horizontal(
            Static("Bind Mounts", id="shares_overview_title"),
            Button("+", id="add_share", variant="default"),
            id="shares_overview_header",
        ),
        _OverviewSelectionList(
            *_share_selection_items(state.built_in_shares, state.custom_shares),
            id="shares_overview_list",
            compact=True,
        ),
    ]


def refresh_shares(container: Any, state: OverviewState) -> None:
    overview = container.query_one("#shares_overview", Vertical)
    if not state.built_in_shares and not state.custom_shares:
        overview.display = False
        return
    overview.display = True
    container.query_one("#shares_overview_title", Static).update("Bind Mounts")
    selection_list = container.query_one("#shares_overview_list", SelectionList)
    selection_list.clear_options()
    selection_list.add_options(
        _share_selection_items(state.built_in_shares, state.custom_shares)
    )


def merge_built_in_shares(
    fresh_items: list[BuiltInShareValue],
    current_items: list[BuiltInShareValue],
) -> list[BuiltInShareValue]:
    current_enabled_by_identity = {
        built_in_identity(item.source, item.key): item.enabled for item in current_items
    }
    return [
        BuiltInShareValue(
            source=item.source,
            key=item.key,
            label=item.label,
            path=item.path,
            persisted=item.persisted,
            enabled=current_enabled_by_identity.get(
                built_in_identity(item.source, item.key), item.enabled
            ),
            row_key=item.row_key,
        )
        for item in fresh_items
    ]


def current_custom_shares(state: OverviewState) -> list[CustomShareValue]:
    return list(state.custom_shares)


def _share_selection_items(
    built_in_shares: list[BuiltInShareValue],
    custom_shares: list[CustomShareValue],
) -> list[tuple[str, str, bool]]:
    return mount_selection_rows(
        overview_mount_list_items(built_in_shares, custom_shares)
    )
