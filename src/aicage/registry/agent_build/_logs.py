from pathlib import Path

from aicage.paths import IMAGE_BUILD_LOG_DIR
from aicage.registry._sanitize import sanitize
from aicage.registry._time import timestamp


def build_log_path(agent: str, base: str) -> Path:
    return IMAGE_BUILD_LOG_DIR / f"{sanitize(agent)}-{base}-{timestamp()}.log"
