import subprocess
import threading
import time
from pathlib import Path

import pytest

from aicage.config.agent.loader import load_agents
from aicage.config.base.loader import load_bases
from aicage.constants import IMAGE_REGISTRY, IMAGE_REPOSITORY
from aicage.docker.query import get_local_repo_digest_for_repo

from .._helpers import require_integration, run_cli_pty, setup_workspace

pytestmark = pytest.mark.integration

_EXPECTED_DIGEST_PARTS: int = 2


def test_builtin_agent_cleans_old_digest_after_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    require_integration()
    docker_args = "--env AICAGE_ENTRYPOINT_CMD=bash"
    workspace, env = setup_workspace(monkeypatch, tmp_path, "copilot", docker_args=docker_args)
    bases = load_bases()
    agents = load_agents(bases)
    image_ref = agents["copilot"].valid_bases["ubuntu"]
    other_ref = agents["codex"].valid_bases["ubuntu"]
    repository = f"{IMAGE_REGISTRY}/{IMAGE_REPOSITORY}"
    subprocess.run(["docker", "pull", image_ref], check=True, capture_output=True)
    subprocess.run(["docker", "pull", other_ref], check=True, capture_output=True)
    old_digest = get_local_repo_digest_for_repo(image_ref, repository)
    assert old_digest is not None
    before_pairs = _repo_digest_pairs()
    assert (repository, old_digest) in before_pairs

    result: dict[str, object] = {}

    def _run_agent() -> None:
        exit_code, output = run_cli_pty(
            ["copilot", "-lc", "sleep 4; echo done"],
            env=env,
            cwd=workspace,
        )
        result["exit_code"] = exit_code
        result["output"] = output

    runner = threading.Thread(target=_run_agent, daemon=True)
    runner.start()
    time.sleep(1.5)
    subprocess.run(["docker", "tag", other_ref, image_ref], check=True, capture_output=True)
    runner.join()
    assert result.get("exit_code") == 0, result.get("output")

    after_pairs = _repo_digest_pairs()
    assert (repository, old_digest) not in after_pairs

    subprocess.run(["docker", "image", "rm", "-f", image_ref], check=False, capture_output=True)
    subprocess.run(["docker", "image", "rm", "-f", other_ref], check=False, capture_output=True)


def _repo_digest_pairs() -> set[tuple[str, str]]:
    result = subprocess.run(
        ["docker", "image", "ls", "--digests", "--format", "{{.Repository}} {{.Digest}}"],
        check=True,
        capture_output=True,
        text=True,
    )
    pairs: set[tuple[str, str]] = set()
    for line in result.stdout.splitlines():
        parts = [part for part in line.strip().split(" ", 1) if part]
        if len(parts) != _EXPECTED_DIGEST_PARTS:
            continue
        repository, digest = parts
        if repository == "<none>" or digest == "<none>":
            continue
        pairs.add((repository, digest))
    return pairs
