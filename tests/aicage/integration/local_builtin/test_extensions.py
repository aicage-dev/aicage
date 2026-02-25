from pathlib import Path

import pytest

from aicage.config.config_store import SettingsStore
from aicage.constants import DEFAULT_EXTENDED_IMAGE_NAME
from aicage.docker.query import local_image_exists
from aicage.registry.agent_build._store import BuildStore as AgentBuildStore
from aicage.registry.extension_build._store import BuildStore as ExtendedBuildStore

from .._helpers import (
    assert_marker_extension_present,
    assert_old_image_replaced,
    assert_rootfs_layer_present,
    copy_marker_extension_sample,
    custom_extensions_dir,
    force_record_agent_version,
    get_last_rootfs_layer,
    replace_with_dummy_image,
    require_integration,
    setup_workspace,
)

pytestmark = pytest.mark.integration


def test_local_builtin_extension_builds_and_runs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    require_integration()
    workspace, env = _setup_extension_workspace(monkeypatch, tmp_path, "claude")
    assert_marker_extension_present(env, workspace, "claude")


def test_local_builtin_extension_rebuilds_on_agent_version(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    require_integration()
    workspace, env = _setup_extension_workspace(monkeypatch, tmp_path, "claude")
    assert_marker_extension_present(env, workspace, "claude")

    store = AgentBuildStore()
    record = store.load("claude", "ubuntu")
    assert record is not None
    force_record_agent_version(store, record, agent_version="0.0.0")
    old_image_ref = replace_with_dummy_image(record.image_ref)
    assert local_image_exists(old_image_ref)

    assert_marker_extension_present(env, workspace, "claude")
    updated = store.load("claude", "ubuntu")
    assert updated is not None
    assert updated.agent_version != "0.0.0"
    assert_old_image_replaced(old_image_ref, record.image_ref)

    extended_record = ExtendedBuildStore().load(f"{DEFAULT_EXTENDED_IMAGE_NAME}:claude-ubuntu-marker")
    assert extended_record is not None
    expected_base_layer = get_last_rootfs_layer(extended_record.base_image)
    assert_rootfs_layer_present(expected_base_layer, extended_record.image_ref)


def test_local_builtin_extension_rebuilds_on_base_layer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    require_integration()
    workspace, env = _setup_extension_workspace(monkeypatch, tmp_path, "claude")
    assert_marker_extension_present(env, workspace, "claude")

    extended_store = ExtendedBuildStore()
    record = extended_store.load(f"{DEFAULT_EXTENDED_IMAGE_NAME}:claude-ubuntu-marker")
    assert record is not None

    expected_base_layer = get_last_rootfs_layer(record.base_image)
    old_image_ref = replace_with_dummy_image(record.image_ref)
    assert local_image_exists(old_image_ref)

    assert_marker_extension_present(env, workspace, "claude")
    assert_old_image_replaced(old_image_ref, record.image_ref)
    assert_rootfs_layer_present(expected_base_layer, record.image_ref)


def _setup_extension_workspace(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    agent_name: str,
) -> tuple[Path, dict[str, str]]:
    workspace, env = setup_workspace(
        monkeypatch,
        tmp_path,
        agent_name,
        docker_args="--env AICAGE_ENTRYPOINT_CMD=bash",
    )
    extension_dir = custom_extensions_dir() / "marker"
    extension_dir.parent.mkdir(parents=True, exist_ok=True)
    copy_marker_extension_sample(extension_dir)

    store = SettingsStore()
    project_cfg = store.load_project(workspace)
    agent_cfg = project_cfg.agents[agent_name]
    agent_cfg.base = "ubuntu"
    agent_cfg.docker_args = "--env AICAGE_ENTRYPOINT_CMD=bash"
    agent_cfg.image_ref = f"{DEFAULT_EXTENDED_IMAGE_NAME}:{agent_name}-ubuntu-marker"
    agent_cfg.extensions = ["marker"]
    store.save_project(workspace, project_cfg)
    return workspace, env
