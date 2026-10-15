from pathlib import Path
from typing import Any

from aicage._logging import get_logger
from aicage.config.config_store import SettingsStore


def remove_agent_config(agent: str, scope: str | None = None) -> None:
    logger = get_logger()
    store = SettingsStore()
    project_path = Path.cwd().resolve()
    config_path, label = _config_path(store, project_path, scope)
    logger.info("Removing agent config '%s' from %s", agent, config_path)
    if not config_path.exists():
        print(f"{label} config not found:")
        print(config_path)
        return
    config = _load_config(store, project_path, scope)
    if agent not in config.agents:
        print("Agent config not found:")
        print(agent)
        return
    del config.agents[agent]
    _save_config(store, project_path, config, scope)
    print("Agent config removed:")
    print(agent)
    print(f"{label} config updated:")
    print(config_path)


def _config_path(
    store: SettingsStore,
    project_path: Path,
    scope: str | None,
) -> tuple[Path, str]:
    if scope == "global":
        return store.global_config_path(), _config_label(scope)
    if scope == "tree":
        return store.tree_config_path(project_path), _config_label(scope)
    return store.project_config_path(project_path), _config_label(scope)


def _config_label(scope: str | None) -> str:
    if scope == "global":
        return "Global"
    if scope == "tree":
        return "Directory tree"
    return "Project"


def _load_config(
    store: SettingsStore,
    project_path: Path,
    scope: str | None,
):
    if scope == "global":
        return store.load_global()
    if scope == "tree":
        return store.load_tree(project_path)
    return store.load_project(project_path)


def _save_config(
    store: SettingsStore,
    project_path: Path,
    config: Any,
    scope: str | None,
) -> None:
    if scope == "global":
        store.save_global(config)
    elif scope == "tree":
        store.save_tree(project_path, config)
    else:
        store.save_project(project_path, config)
