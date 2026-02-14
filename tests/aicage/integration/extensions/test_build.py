from pathlib import Path

import pytest

from aicage.config.config_store import SettingsStore
from aicage.constants import DEFAULT_EXTENDED_IMAGE_NAME, IMAGE_REGISTRY, IMAGE_REPOSITORY
from aicage.docker.query import local_image_exists
from aicage.registry.extension_build._extended_store import ExtendedBuildStore

from .._helpers import (
    assert_base_layer_present,
    assert_marker_extension_present,
    copy_marker_extension_sample,
    custom_extensions_dir,
    replace_with_dummy_image,
    require_integration,
    setup_workspace,
)

pytestmark = pytest.mark.integration


def test_extension_builds_and_runs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    require_integration()
    workspace, env = setup_workspace(
        monkeypatch,
        tmp_path,
        "codex",
        docker_args="--env AICAGE_ENTRYPOINT_CMD=bash",
    )

    extension_dir = custom_extensions_dir() / "marker"
    extension_dir.parent.mkdir(parents=True, exist_ok=True)
    copy_marker_extension_sample(extension_dir)

    store = SettingsStore()
    project_cfg = store.load_project(workspace)
    agent_cfg = project_cfg.agents["codex"]
    agent_cfg.base = "ubuntu"
    agent_cfg.docker_args = "--env AICAGE_ENTRYPOINT_CMD=bash"
    agent_cfg.image_ref = f"{DEFAULT_EXTENDED_IMAGE_NAME}:codex-ubuntu-marker"
    agent_cfg.extensions = ["marker"]
    store.save_project(workspace, project_cfg)

    image_repository = f"{IMAGE_REGISTRY}/{IMAGE_REPOSITORY}"
    local_base_image_ref = f"{image_repository}:codex-ubuntu"
    old_digest = replace_with_dummy_image(local_base_image_ref)
    old_digest_ref = f"{image_repository}@{old_digest}"
    assert local_image_exists(old_digest_ref)

    assert_marker_extension_present(env, workspace, "codex")
    assert not local_image_exists(old_digest_ref)


def test_extension_rebuilds_on_base_image_change(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    require_integration()
    workspace, env = setup_workspace(
        monkeypatch,
        tmp_path,
        "copilot",
        docker_args="--env AICAGE_ENTRYPOINT_CMD=bash",
    )

    extension_dir = custom_extensions_dir() / "marker"
    extension_dir.parent.mkdir(parents=True, exist_ok=True)
    copy_marker_extension_sample(extension_dir)

    store = SettingsStore()
    project_cfg = store.load_project(workspace)
    agent_cfg = project_cfg.agents["copilot"]
    agent_cfg.base = "ubuntu"
    agent_cfg.docker_args = "--env AICAGE_ENTRYPOINT_CMD=bash"
    agent_cfg.image_ref = f"{DEFAULT_EXTENDED_IMAGE_NAME}:copilot-ubuntu-marker"
    agent_cfg.extensions = ["marker"]
    store.save_project(workspace, project_cfg)

    assert_marker_extension_present(env, workspace, "copilot")

    extended_store = ExtendedBuildStore()
    record = extended_store.load(f"{DEFAULT_EXTENDED_IMAGE_NAME}:copilot-ubuntu-marker")
    assert record is not None

    replace_with_dummy_image(record.base_image)

    assert_marker_extension_present(env, workspace, "copilot")
    assert_base_layer_present(record.base_image, record.image_ref)
