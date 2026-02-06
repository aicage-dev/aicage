import subprocess
from pathlib import Path

import pytest
import yaml

from aicage.config.config_store import SettingsStore
from aicage.registry.local_build._custom_base import custom_base_image_ref

from .._helpers import (
    copy_custom_base_sample,
    custom_bases_dir,
    require_integration,
    run_agent_version,
    setup_workspace,
)

pytestmark = pytest.mark.integration


def test_custom_base_cleans_old_digest_after_build(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    require_integration()
    base_name = "php"
    workspace, env = setup_workspace(monkeypatch, tmp_path, "codex")
    base_dir = custom_bases_dir() / base_name
    base_dir.parent.mkdir(parents=True, exist_ok=True)
    copy_custom_base_sample(base_name, base_dir)

    store = SettingsStore()
    project_cfg = store.load_project(workspace)
    agent_cfg = project_cfg.agents["codex"]
    agent_cfg.base = base_name
    store.save_project(workspace, project_cfg)

    run_agent_version(env, workspace, "codex")
    image_ref = custom_base_image_ref(base_name)
    old_id = _image_id(image_ref)

    _update_from_image(base_dir, "php:8.2")
    run_agent_version(env, workspace, "codex")
    new_id = _image_id(image_ref)

    assert new_id != old_id


def _update_from_image(base_dir: Path, from_image: str) -> None:
    definition_path = base_dir / "base.yml"
    payload = yaml.safe_load(definition_path.read_text(encoding="utf-8")) or {}
    payload["from_image"] = from_image
    definition_path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")


def _image_id(image_ref: str) -> str:
    result = subprocess.run(
        ["docker", "image", "inspect", "-f", "{{.Id}}", image_ref],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()
