from pathlib import Path

from aicage._logging import get_logger
from aicage.config.config_store import SettingsStore


def remove_project_config(agent: str | None = None) -> None:
    logger = get_logger()
    store = SettingsStore()
    project_path = Path.cwd().resolve()
    config_path = store.project_config_path(project_path)
    if agent is not None:
        _remove_agent_config(store, project_path, config_path, agent)
        return
    logger.info("Removing project config at %s", config_path)
    if config_path.exists():
        config_path.unlink()
        print("Project config removed:")
        print(config_path)
    else:
        print("Project config not found:")
        print(config_path)


def _remove_agent_config(
    store: SettingsStore,
    project_path: Path,
    config_path: Path,
    agent: str,
) -> None:
    logger = get_logger()
    logger.info("Removing agent config '%s' from %s", agent, config_path)
    if not config_path.exists():
        print("Project config not found:")
        print(config_path)
        return
    config = store.load_project(project_path)
    if agent not in config.agents:
        print("Agent config not found:")
        print(agent)
        return
    del config.agents[agent]
    store.save_project(project_path, config)
    print("Agent config removed:")
    print(agent)
    print("Project config updated:")
    print(config_path)
