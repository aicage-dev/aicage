from dataclasses import dataclass

from aicage.config.project_config import (
    MOUNT_GITCONFIG_KEY,
    MOUNT_GITROOT_KEY,
    MOUNT_GNUPG_KEY,
    MOUNT_SSH_KEY,
)

from ._ids import custom_share_selection_key
from ._models import BuiltInShareValue, CustomShareValue
from ._mount_value import display_mount_value, split_mount_value
from .services.host_access import built_in_selection_value

_READ_ONLY_PREFIX = "Read-only"
_GIT_SUPPORT_LABELS: dict[str, str] = {
    MOUNT_GITCONFIG_KEY: "Git config",
    MOUNT_GITROOT_KEY: "Git root",
    MOUNT_SSH_KEY: "SSH",
    MOUNT_GNUPG_KEY: "GnuPG",
}


@dataclass(frozen=True)
class _MountListItem:
    prefix: str | None
    path: str
    selection_key: str
    enabled: bool


def git_support_label(key: str) -> str:
    return _GIT_SUPPORT_LABELS.get(key, key)


def extension_label(extension_id: str) -> str:
    return f"Extension {extension_id}"


def overview_mount_list_items(
    built_in_shares: list[BuiltInShareValue],
    custom_shares: list[CustomShareValue],
) -> list[_MountListItem]:
    items = [
        _MountListItem(
            prefix=item.label,
            path=display_mount_value(item.path),
            selection_key=built_in_selection_value(item),
            enabled=item.enabled,
        )
        for item in built_in_shares
    ]
    items.extend(_custom_mount_list_item(item) for item in custom_shares)
    return items


def confirm_mount_list_items(shares: list[BuiltInShareValue]) -> list[_MountListItem]:
    return [
        _MountListItem(
            prefix=item.label,
            path=display_mount_value(item.path),
            selection_key=built_in_selection_value(item),
            enabled=item.enabled,
        )
        for item in shares
    ]


def mount_selection_rows(items: list[_MountListItem]) -> list[tuple[str, str, bool]]:
    prefix_width = max((len(item.prefix or "") for item in items), default=0)
    return [
        (_format_mount_label(item, prefix_width), item.selection_key, item.enabled)
        for item in items
    ]


def _custom_mount_list_item(item: CustomShareValue) -> _MountListItem:
    path, read_only = split_mount_value(item.value)
    return _MountListItem(
        prefix=_READ_ONLY_PREFIX if read_only else None,
        path=path,
        selection_key=custom_share_selection_key(item.value),
        enabled=True,
    )


def _format_mount_label(item: _MountListItem, prefix_width: int) -> str:
    if prefix_width == 0:
        return item.path
    return f"{(item.prefix or ''):<{prefix_width}}: {item.path}"
