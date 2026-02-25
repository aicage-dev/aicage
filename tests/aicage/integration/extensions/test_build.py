from pathlib import Path

import pytest

from aicage.constants import IMAGE_REGISTRY, IMAGE_REPOSITORY
from aicage.docker.query import local_image_exists
from aicage.registry.extension_build._store import BuildStore

from .._helpers import (
    assert_marker_extension_present,
    assert_old_image_replaced,
    assert_rootfs_layer_present,
    keep_pulled_image_last_rootfs_layer,
    replace_with_dummy_image,
    resolve_remote_digest_ref,
    setup_marker_extension_workspace,
)

pytestmark = pytest.mark.integration


def test_extension_builds_and_runs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workspace, env, _ = setup_marker_extension_workspace(
        monkeypatch,
        tmp_path,
        "codex",
    )

    image_repository = f"{IMAGE_REGISTRY}/{IMAGE_REPOSITORY}"
    local_base_image_ref = f"{image_repository}:codex-ubuntu"
    old_image_ref = replace_with_dummy_image(local_base_image_ref)
    assert local_image_exists(old_image_ref)

    assert_marker_extension_present(env, workspace, "codex")
    assert_old_image_replaced(old_image_ref, local_base_image_ref)


def test_extension_rebuilds_on_base_image_change(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    workspace, env, image_ref = setup_marker_extension_workspace(
        monkeypatch,
        tmp_path,
        "copilot",
    )

    assert_marker_extension_present(env, workspace, "copilot")

    extended_store = BuildStore()
    record = extended_store.load(image_ref)
    assert record is not None

    base_digest_ref = resolve_remote_digest_ref(record.base_image)
    with keep_pulled_image_last_rootfs_layer(base_digest_ref) as expected_base_layer:
        old_base_image_ref = replace_with_dummy_image(record.base_image)
        assert local_image_exists(old_base_image_ref)

        assert_marker_extension_present(env, workspace, "copilot")
        assert_old_image_replaced(old_base_image_ref, record.base_image)
        assert_rootfs_layer_present(expected_base_layer, record.image_ref)
