import os

from aicage.runtime.env_vars import AICAGE_GID, AICAGE_UID, AICAGE_USER


def resolve_user_ids() -> list[str]:
    env_flags: list[str] = []
    if os.name == "nt":
        user = "root"
        env_flags.extend(["-e", f"{AICAGE_USER}={user}"])
        return env_flags

    getuid = getattr(os, "getuid", None)
    getgid = getattr(os, "getgid", None)
    uid = getuid() if callable(getuid) else None
    gid = getgid() if callable(getgid) else None

    user = os.environ.get("USER") or os.environ.get("USERNAME") or "aicage"
    if uid is not None:
        env_flags.extend(["-e", f"{AICAGE_UID}={uid}", "-e", f"{AICAGE_GID}{'='}{gid}"])
    env_flags.extend(["-e", f"{AICAGE_USER}={user}"])
    return env_flags
