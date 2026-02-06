import subprocess
from pathlib import Path

import pytest

from aicage.constants import IMAGE_BASE_REPOSITORY, IMAGE_REGISTRY
from aicage.docker.query import get_local_repo_digest_for_repo
from aicage.registry.local_build._store import BuildStore

from .._helpers import (
    force_record_agent_version,
    require_integration,
    run_agent_version,
    setup_workspace,
)

pytestmark = pytest.mark.integration

_EXPECTED_DIGEST_PARTS: int = 2


def test_local_builtin_cleans_old_digest_after_build(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    require_integration()
    workspace, env = setup_workspace(monkeypatch, tmp_path, "claude")
    run_agent_version(env, workspace, "claude")

    store = BuildStore()
    record = store.load("claude", "ubuntu")
    assert record is not None

    base_repository = f"{IMAGE_REGISTRY}/{IMAGE_BASE_REPOSITORY}"
    base_ref = f"{base_repository}:ubuntu"
    other_ref = f"{base_repository}:alpine"
    subprocess.run(["docker", "pull", other_ref], check=True, capture_output=True)
    old_digest = get_local_repo_digest_for_repo(other_ref, base_repository)
    assert old_digest is not None
    subprocess.run(["docker", "tag", other_ref, base_ref], check=True, capture_output=True)
    subprocess.run(["docker", "image", "rm", other_ref], check=True, capture_output=True)
    local_digest = get_local_repo_digest_for_repo(base_ref, base_repository)
    assert local_digest == old_digest

    force_record_agent_version(store, record, agent_version="0.0.0")
    run_agent_version(env, workspace, "claude")

    assert (base_repository, old_digest) not in _repo_digest_pairs()


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
