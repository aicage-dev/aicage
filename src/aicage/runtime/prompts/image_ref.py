from aicage._logging import get_logger

from ...constants import DEFAULT_EXTENDED_IMAGE_NAME
from ._tty import ensure_tty_for_prompt
from .mode import assume_yes_enabled


def prompt_for_image_ref(default_ref: str) -> str:
    if assume_yes_enabled():
        get_logger().info("Selected image ref '%s' (assume-yes)", default_ref)
        return default_ref
    ensure_tty_for_prompt()
    response = input(f"Enter image name:tag [{default_ref}]: ").strip()
    if not response:
        return default_ref
    if ":" not in response:
        return f"{DEFAULT_EXTENDED_IMAGE_NAME}:{response}"
    return response
