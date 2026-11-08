"""SSH and GnuPG key-access selection support."""

from typing import Protocol

from aicage.config.project_config import MOUNT_GNUPG_KEY, MOUNT_SSH_KEY
from aicage.gpg import has_gpg_keys, resolve_gpg_home
from aicage.paths import HOST_SSH_DIR
from aicage.runtime._ssh_agent import _has_ssh_keys


class _SshGnuPgMountPrefs(Protocol):
    gnupg: bool | None
    ssh: bool | None


def ssh_gnupg_mount_defaults(mounts_cfg: _SshGnuPgMountPrefs) -> set[str]:
    return {
        key
        for key, _description in _ssh_gnupg_prompt_items(mounts_cfg)
        if getattr(mounts_cfg, key) is None
    }


def _ssh_gnupg_prompt_items(
    mounts_cfg: _SshGnuPgMountPrefs,
) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    if _has_ssh_keys() and mounts_cfg.ssh is None:
        items.append((MOUNT_SSH_KEY, f"SSH agent: {HOST_SSH_DIR}"))
    if has_gpg_keys() and mounts_cfg.gnupg is None:
        gpg_home = resolve_gpg_home()
        if gpg_home is not None:
            items.append((MOUNT_GNUPG_KEY, f"GnuPG agent: {gpg_home}"))
    return items
