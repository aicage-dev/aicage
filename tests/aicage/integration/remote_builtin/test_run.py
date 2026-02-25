from pathlib import Path

import pytest

from aicage.config.agent.loader import load_agents
from aicage.config.base.loader import load_bases
from aicage.docker.query import local_image_exists

from .._helpers import (
    assert_old_image_replaced,
    replace_with_dummy_image,
    require_integration,
    run_agent_version,
    setup_workspace,
)

pytestmark = pytest.mark.integration


def test_builtin_agent_runs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    require_integration()
    workspace, env = setup_workspace(monkeypatch, tmp_path, "codex")
    bases = load_bases()
    agents = load_agents(bases)
    image_ref = agents["codex"].valid_bases["ubuntu"]
    old_image_ref = replace_with_dummy_image(image_ref)
    assert local_image_exists(old_image_ref)
    run_agent_version(env, workspace, "codex")
    assert_old_image_replaced(old_image_ref, image_ref)
