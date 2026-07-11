from aicage.config.run_config_draft import RunConfigDraft

from .._models import CustomShareValue, ShareEditorResult
from .._state import OverviewState
from ._share_support import normalize_shares_from_editor


def add_custom_share(state: OverviewState, draft: RunConfigDraft, share: str) -> bool:
    normalized = normalize_shares_from_editor(draft, [share])
    if not normalized:
        return False
    share_value = normalized[0]
    if any(item.value == share_value for item in state.custom_shares):
        return False
    state.custom_shares.append(CustomShareValue(share_value))
    return True


def update_custom_share(
    state: OverviewState,
    draft: RunConfigDraft,
    current_value: str,
    result: ShareEditorResult,
) -> bool:
    if result.remove:
        state.custom_shares = [item for item in state.custom_shares if item.value != current_value]
        return True
    if result.share is None:
        return False
    normalized = normalize_shares_from_editor(draft, [result.share])
    if not normalized:
        return False
    share_value = normalized[0]
    if share_value == current_value:
        return False
    if any(item.value == share_value for item in state.custom_shares):
        return False
    state.custom_shares = [
        CustomShareValue(share_value) if item.value == current_value else item
        for item in state.custom_shares
    ]
    return True
