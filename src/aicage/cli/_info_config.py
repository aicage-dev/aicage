from pathlib import Path

from aicage._logging import get_logger
from aicage.config.config_store import SettingsStore


def info_project_config(scope: str | None = None) -> None:
    logger = get_logger()
    store = SettingsStore()
    project_path = Path.cwd().resolve()
    config_path, label = _config_path(store, project_path, scope)
    logger.info("Printing %s config at %s", label.lower(), config_path)
    print(f"{label} config path:")
    print(config_path)
    print()
    print("Project config content:")
    if config_path.exists():
        contents = config_path.read_text(encoding="utf-8").rstrip()
        if contents:
            print(contents)
        else:
            print("(empty)")
    else:
        print("(missing)")


def _config_path(
    store: SettingsStore,
    project_path: Path,
    scope: str | None,
) -> tuple[Path, str]:
    if scope == "global":
        return store.global_config_path(), "Global"
    if scope == "tree":
        return store.tree_config_path(project_path), "Directory tree"
    return store.project_config_path(project_path), "Project"
