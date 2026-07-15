from aicage._logging import get_logger
from aicage.constants import DEFAULT_EXTENDED_IMAGE_NAME

from ._tty import ensure_tty_for_prompt
from .mode import non_interactive_defaults_enabled


def prompt_for_image_ref(default_ref: str) -> str:
    if non_interactive_defaults_enabled():
        get_logger().info(
            "Selected image ref '%s' (non-interactive defaults)", default_ref
        )
        return default_ref
    ensure_tty_for_prompt()
    response = input(f"Enter image name:tag [{default_ref}]: ").strip()
    if not response:
        return default_ref
    if ":" not in response:
        return f"{DEFAULT_EXTENDED_IMAGE_NAME}:{response}"
    return response
