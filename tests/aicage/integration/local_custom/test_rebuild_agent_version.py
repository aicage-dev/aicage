from pathlib import Path

import pytest

from aicage.docker.query import local_image_exists
from aicage.docker.refs import repository_from_image_ref
from aicage.registry.agent_build._store import BuildStore

from .._helpers import (
    copy_forge_sample,
    custom_agents_dir,
    force_record_agent_version,
    replace_with_dummy_image,
    require_integration,
    run_agent_version,
    setup_workspace,
)

pytestmark = pytest.mark.integration


def test_custom_agent_rebuilds(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    require_integration()
    workspace, env = setup_workspace(monkeypatch, tmp_path, "forge")
    agent_dir = custom_agents_dir() / "forge"
    copy_forge_sample(agent_dir)

    run_agent_version(env, workspace, "forge")
    store = BuildStore()
    record = store.load("forge", "ubuntu")
    assert record is not None

    force_record_agent_version(
        store,
        record,
        agent_version="0.0.0",
    )
    old_digest = replace_with_dummy_image(record.image_ref)
    old_digest_ref = f"{repository_from_image_ref(record.image_ref)}@{old_digest}"
    assert local_image_exists(old_digest_ref)
    run_agent_version(env, workspace, "forge")
    updated = store.load("forge", "ubuntu")
    assert updated is not None
    assert updated.agent_version != "0.0.0"
    assert not local_image_exists(old_digest_ref)
