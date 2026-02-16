from pathlib import Path

import pytest

from aicage.config.agent.loader import load_agents
from aicage.config.base.loader import load_bases
from aicage.constants import IMAGE_REGISTRY, IMAGE_REPOSITORY
from aicage.docker.query import get_local_repo_digest_for_repo, local_image_exists

from .._helpers import (
    copy_forge_sample,
    custom_agents_dir,
    replace_with_dummy_image,
    require_integration,
    require_proxy_integration,
    run_agent_version,
    run_cli_pty,
    setup_workspace,
)

pytestmark = [pytest.mark.integration, pytest.mark.proxy_integration]


def test_proxy_host_and_runtime_network(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    require_integration()
    require_proxy_integration()
    workspace, env = setup_workspace(
        monkeypatch,
        tmp_path,
        "codex",
        docker_args="--env AICAGE_ENTRYPOINT_CMD=bash",
    )
    bases = load_bases()
    agents = load_agents(bases)
    image_ref = agents["codex"].valid_bases["ubuntu"]
    local_digest_before = replace_with_dummy_image(image_ref)
    repository = f"{IMAGE_REGISTRY}/{IMAGE_REPOSITORY}"
    old_digest_ref = f"{repository}@{local_digest_before}"
    assert local_image_exists(old_digest_ref)

    exit_code, output = run_cli_pty(
        ["codex", "-lc", "curl -fsS https://api.github.com >/dev/null"],
        env=env,
        cwd=workspace,
        input_data="\n\n",
    )
    assert exit_code == 0, output
    local_digest_after = get_local_repo_digest_for_repo(image_ref, repository)
    assert local_digest_after is not None
    assert local_digest_after != local_digest_before
    assert not local_image_exists(old_digest_ref)


def test_proxy_custom_agent_build_and_version(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    require_integration()
    require_proxy_integration()
    workspace, env = setup_workspace(monkeypatch, tmp_path, "forge")
    copy_forge_sample(custom_agents_dir() / "forge")

    run_agent_version(env, workspace, "forge")
