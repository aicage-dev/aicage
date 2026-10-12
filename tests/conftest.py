from pathlib import Path

import pytest

from aicage.config import config_store


@pytest.fixture(autouse=True)
def _isolate_persisted_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(config_store, "PROJECTS_DIR", tmp_path / "projects")
    monkeypatch.setattr(
        config_store, "GLOBAL_CONFIG_PATH", tmp_path / "config/global.yml"
    )
    monkeypatch.setattr(config_store, "TREES_DIR", tmp_path / "config/trees")
