from pathlib import Path

import pytest

from aicage.docker.query import local_image_exists
from aicage.docker.refs import repository_from_image_ref
from aicage.registry.agent_build._store import BuildStore

from .._helpers import (
    assert_rootfs_layer_present,
    keep_pulled_image_last_rootfs_layer,
    replace_with_dummy_image,
    require_integration,
    run_agent_version,
    setup_workspace,
)

pytestmark = pytest.mark.integration


def test_local_builtin_agent_rebuilds_on_base_layer(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    require_integration()
    workspace, env = setup_workspace(monkeypatch, tmp_path, "claude")
    run_agent_version(env, workspace, "claude")

    store = BuildStore()
    record = store.load("claude", "ubuntu")
    assert record is not None
    source_image_ref = f"{repository_from_image_ref(record.base_image)}:ubuntu"
    assert local_image_exists(source_image_ref)

    with keep_pulled_image_last_rootfs_layer(record.base_image) as expected_base_layer:
        old_digest = replace_with_dummy_image(record.image_ref)
        old_digest_ref = f"{repository_from_image_ref(record.image_ref)}@{old_digest}"
        assert local_image_exists(old_digest_ref)
        run_agent_version(env, workspace, "claude")
        updated = store.load("claude", "ubuntu")
        assert updated is not None
        assert not local_image_exists(old_digest_ref)
        assert local_image_exists(source_image_ref)
        assert_rootfs_layer_present(expected_base_layer, record.image_ref)
