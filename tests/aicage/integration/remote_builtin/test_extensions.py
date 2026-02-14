from pathlib import Path

import pytest

from aicage.docker.query import get_local_repo_digest_for_repo, local_image_exists
from aicage.docker.refs import repository_from_image_ref
from aicage.registry.extension_build._extended_store import ExtendedBuildStore

from .._helpers import (
    assert_base_layer_present,
    assert_marker_extension_present,
    replace_with_dummy_image,
    setup_marker_extension_workspace,
)

pytestmark = pytest.mark.integration


def test_remote_builtin_extension_rebuilds_on_base_change(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    workspace, env, image_ref = setup_marker_extension_workspace(
        monkeypatch,
        tmp_path,
        "codex",
    )

    assert_marker_extension_present(env, workspace, "codex")

    extended_store = ExtendedBuildStore()
    record = extended_store.load(image_ref)
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
