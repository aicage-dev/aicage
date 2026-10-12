import hashlib
from pathlib import Path
from typing import Any

import yaml

from aicage.paths import GLOBAL_CONFIG_PATH, PROJECTS_DIR, TREES_DIR

from ._yaml_loader import load_yaml
from .project_config import _ProjectConfig


class _IndentedSafeDumper(yaml.SafeDumper):
    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:
        super().increase_indent(flow, False)


class SettingsStore:
    """
    Persists per-project configuration under ~/.aicage.
    """

    def __init__(self) -> None:
        self.projects_dir = PROJECTS_DIR
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.trees_dir = TREES_DIR
        self.trees_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _save_yaml(path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            yaml.dump(data, handle, Dumper=_IndentedSafeDumper, sort_keys=True)

    def _project_path(self, project_realpath: Path) -> Path:
        digest = hashlib.sha256(str(project_realpath).encode("utf-8")).hexdigest()
        return self.projects_dir / f"{digest}.yml"

    def load_project(self, project_realpath: Path) -> _ProjectConfig:
        path = self._project_path(project_realpath)
        if not path.exists():
            data = {}
        else:
            data = load_yaml(path)
        return _ProjectConfig.from_mapping(project_realpath, data)

    def save_project(self, project_realpath: Path, config: _ProjectConfig) -> None:
        self._save_yaml(self._project_path(project_realpath), config.to_mapping())

    def load_global(self) -> _ProjectConfig:
        return self._load(GLOBAL_CONFIG_PATH, Path("/"))

    def save_global(self, config: _ProjectConfig) -> None:
        self._save_yaml(GLOBAL_CONFIG_PATH, config.to_mapping())

    def load_tree(self, directory_realpath: Path) -> _ProjectConfig:
        return self._load(self._tree_path(directory_realpath), directory_realpath)

    def save_tree(self, directory_realpath: Path, config: _ProjectConfig) -> None:
        self._save_yaml(self._tree_path(directory_realpath), config.to_mapping())

    def project_config_path(self, project_realpath: Path) -> Path:
        """
        Returns the path to a project's config file under the base directory.
        """
        return self._project_path(project_realpath)

    def global_config_path(self) -> Path:
        return GLOBAL_CONFIG_PATH

    def tree_config_path(self, directory_realpath: Path) -> Path:
        return self._tree_path(directory_realpath)

    def _tree_path(self, directory_realpath: Path) -> Path:
        digest = hashlib.sha256(str(directory_realpath).encode("utf-8")).hexdigest()
        return self.trees_dir / f"{digest}.yml"

    @staticmethod
    def _load(path: Path, config_path: Path) -> _ProjectConfig:
        data = load_yaml(path) if path.exists() else {}
        return _ProjectConfig.from_mapping(config_path, data)
