from pathlib import Path

import pytest

from aicage.config.config_store import SettingsStore
from aicage.constants import DEFAULT_EXTENDED_IMAGE_NAME
from aicage.docker.query import get_local_repo_digest_for_repo, local_image_exists
from aicage.docker.refs import repository_from_image_ref
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


def test_remote_builtin_extension_rebuilds_on_base_change(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
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

    assert_marker_extension_present(env, workspace, "codex")

    extended_store = ExtendedBuildStore()
    record = extended_store.load(f"{DEFAULT_EXTENDED_IMAGE_NAME}:codex-ubuntu-marker")
    assert record is not None

    digest_after_dummy = replace_with_dummy_image(record.base_image)
    base_repository = repository_from_image_ref(record.base_image)
    old_digest_ref = f"{base_repository}@{digest_after_dummy}"
    assert local_image_exists(old_digest_ref)

    assert_marker_extension_present(env, workspace, "codex")

    digest_after_rebuild = get_local_repo_digest_for_repo(record.base_image, base_repository)
    assert digest_after_rebuild is not None
    assert digest_after_rebuild != digest_after_dummy
    assert not local_image_exists(old_digest_ref)
    assert_base_layer_present(record.base_image, record.image_ref)
