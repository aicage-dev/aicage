import os
from pathlib import Path

from aicage.paths import container_project_path
from aicage.runtime.env_vars import AICAGE_GID, AICAGE_HOME, AICAGE_HOST_IS_LINUX, AICAGE_HOST_USER, AICAGE_UID


def resolve_user_ids() -> list[str]:
    env_flags: list[str] = []
    host_home = _resolve_host_home()
    host_home_posix = container_project_path(host_home).as_posix()
    if os.name == "nt":
        env_flags.extend(["-e", f"{AICAGE_HOME}={host_home_posix}"])
        return env_flags

    getuid = getattr(os, "getuid", None)
    getgid = getattr(os, "getgid", None)
    uid = getuid() if callable(getuid) else None
    gid = getgid() if callable(getgid) else None

    user = _resolve_host_user()
    if uid is not None:
        env_flags.extend(["-e", f"{AICAGE_UID}={uid}", "-e", f"{AICAGE_GID}{'='}{gid}"])
    env_flags.extend(["-e", f"{AICAGE_HOST_USER}={user}"])
    env_flags.extend(
        [
            "-e",
            f"{AICAGE_HOME}={host_home_posix}",
            "-e",
            f"{AICAGE_HOST_IS_LINUX}=true",
        ]
    )
    return env_flags


def _resolve_host_user() -> str:
    return os.environ.get("USERNAME") or os.environ.get("USER") or "aicage"


def _resolve_host_home() -> Path:
    return Path.home()
