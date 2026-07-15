from pathlib import Path

import pytest

from aicage.docker.query import local_image_exists
from aicage.registry.agent_build._store import BuildStore

from .._helpers import (
    assert_old_image_replaced,
    force_record_agent_version,
    replace_with_dummy_image,
    require_integration,
    run_agent_version,
    setup_workspace,
)

pytestmark = pytest.mark.integration


def test_local_builtin_agent_rebuilds(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    require_integration()
    workspace, env = setup_workspace(monkeypatch, tmp_path, "claude")
    run_agent_version(env, workspace, "claude")

    store = BuildStore()
    record = store.load("claude", "ubuntu")
    assert record is not None

    force_record_agent_version(
        store,
        record,
        agent_version="0.0.0",
    )
    old_image_ref = replace_with_dummy_image(record.image_ref)
    assert local_image_exists(old_image_ref)
    run_agent_version(env, workspace, "claude")
    updated = store.load("claude", "ubuntu")
    assert updated is not None
    assert updated.agent_version != "0.0.0"
    assert_old_image_replaced(old_image_ref, record.image_ref)
