from pathlib import Path

import pytest

from aicage.constants import IMAGE_REGISTRY, IMAGE_REPOSITORY
from aicage.docker.query import local_image_exists
from aicage.registry.extension_build._extended_store import ExtendedBuildStore

from .._helpers import (
    assert_base_layer_present,
    assert_marker_extension_present,
    replace_with_dummy_image,
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
    old_digest = replace_with_dummy_image(local_base_image_ref)
    old_digest_ref = f"{image_repository}@{old_digest}"
    assert local_image_exists(old_digest_ref)

    assert_marker_extension_present(env, workspace, "codex")
    assert not local_image_exists(old_digest_ref)


def test_extension_rebuilds_on_base_image_change(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    workspace, env, image_ref = setup_marker_extension_workspace(
        monkeypatch,
        tmp_path,
        "copilot",
    )

    assert_marker_extension_present(env, workspace, "copilot")

    extended_store = ExtendedBuildStore()
    record = extended_store.load(image_ref)
    assert record is not None

    replace_with_dummy_image(record.base_image)

    assert_marker_extension_present(env, workspace, "copilot")
    assert_base_layer_present(record.base_image, record.image_ref)
