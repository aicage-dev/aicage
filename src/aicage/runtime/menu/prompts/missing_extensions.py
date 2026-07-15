from pathlib import Path

from aicage._logging import get_logger

from ._tty import ensure_tty_for_prompt
from .mode import non_interactive_defaults_enabled

_DEFAULT_MISSING_EXTENSIONS_CHOICE: str = "exit"


def prompt_for_missing_extensions(
    agent: str,
    missing: list[str],
    stored_image_ref: str,
    project_config_path: Path,
    other_projects: list[tuple[str, Path]],
) -> str:
    if non_interactive_defaults_enabled():
        get_logger().info(
            "Missing extensions prompt choice for '%s' -> %s (non-interactive defaults)",
            agent,
            _DEFAULT_MISSING_EXTENSIONS_CHOICE,
        )
        return _DEFAULT_MISSING_EXTENSIONS_CHOICE
    ensure_tty_for_prompt()
    print(f"[aicage] Missing extensions for '{agent}': {', '.join(sorted(missing))}.")
    if stored_image_ref:
        print(f"[aicage] Stored image ref: {stored_image_ref}")
    print(f"[aicage] Project config: {project_config_path}")
    if other_projects:
        print("[aicage] Other projects using this image:")
        for project_path, config_path in other_projects:
            print(f"  {project_path} -> {config_path}")
    return input("Choose 'exit' or 'fresh': ").strip().lower()
