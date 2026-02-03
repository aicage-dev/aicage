import os

from aicage.runtime.env_vars import AICAGE_GID, AICAGE_HOST_USER, AICAGE_UID, AICAGE_USER


def resolve_user_ids() -> list[str]:
    env_flags: list[str] = []
    host_user = _resolve_host_user()
    if os.name == "nt":
        user = "root"
        env_flags.extend(["-e", f"{AICAGE_USER}={user}", "-e", f"{AICAGE_HOST_USER}={host_user}"])
        return env_flags

    getuid = getattr(os, "getuid", None)
    getgid = getattr(os, "getgid", None)
    uid = getuid() if callable(getuid) else None
    gid = getgid() if callable(getgid) else None

    user = os.environ.get("USER") or os.environ.get("USERNAME") or "aicage"
    if uid is not None:
        env_flags.extend(["-e", f"{AICAGE_UID}={uid}", "-e", f"{AICAGE_GID}{'='}{gid}"])
    env_flags.extend(["-e", f"{AICAGE_USER}={user}", "-e", f"{AICAGE_HOST_USER}={user}"])
    return env_flags


def _resolve_host_user() -> str:
    return os.environ.get("USERNAME") or os.environ.get("USER") or "aicage"
