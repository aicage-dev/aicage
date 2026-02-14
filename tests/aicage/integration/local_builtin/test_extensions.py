from pathlib import Path

import pytest

from aicage.config.config_store import SettingsStore
from aicage.constants import DEFAULT_EXTENDED_IMAGE_NAME
from aicage.docker.query import local_image_exists
from aicage.docker.refs import repository_from_image_ref
from aicage.registry.extension_build._extended_store import ExtendedBuildStore
from aicage.registry.local_build._store import BuildStore

from .._helpers import (
    assert_base_layer_present,
    assert_marker_extension_present,
    copy_marker_extension_sample,
    custom_extensions_dir,
    force_record_agent_version,
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

    store = BuildStore()
    record = store.load("claude", "ubuntu")
    assert record is not None
    force_record_agent_version(store, record, agent_version="0.0.0")
    old_digest = replace_with_dummy_image(record.image_ref)
    old_digest_ref = f"{repository_from_image_ref(record.image_ref)}@{old_digest}"
    assert local_image_exists(old_digest_ref)

    assert_marker_extension_present(env, workspace, "claude")
    updated = store.load("claude", "ubuntu")
    assert updated is not None
    assert updated.agent_version != "0.0.0"
    assert not local_image_exists(old_digest_ref)

    extended_record = ExtendedBuildStore().load(f"{DEFAULT_EXTENDED_IMAGE_NAME}:claude-ubuntu-marker")
    assert extended_record is not None
    assert_base_layer_present(extended_record.base_image, extended_record.image_ref)


def test_local_builtin_extension_rebuilds_on_base_layer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    require_integration()
    workspace, env = _setup_extension_workspace(monkeypatch, tmp_path, "claude")
    assert_marker_extension_present(env, workspace, "claude")

    extended_store = ExtendedBuildStore()
    record = extended_store.load(f"{DEFAULT_EXTENDED_IMAGE_NAME}:claude-ubuntu-marker")
    assert record is not None

    old_digest = replace_with_dummy_image(record.image_ref)
    old_digest_ref = f"{repository_from_image_ref(record.image_ref)}@{old_digest}"
    assert local_image_exists(old_digest_ref)

    assert_marker_extension_present(env, workspace, "claude")
    assert not local_image_exists(old_digest_ref)
    assert_base_layer_present(record.base_image, record.image_ref)


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
