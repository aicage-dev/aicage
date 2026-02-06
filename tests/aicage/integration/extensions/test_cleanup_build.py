import subprocess
from pathlib import Path

import pytest

from aicage.config.config_store import SettingsStore
from aicage.constants import DEFAULT_EXTENDED_IMAGE_NAME, IMAGE_REGISTRY, IMAGE_REPOSITORY
from aicage.docker.query import get_local_repo_digest_for_repo

from .._helpers import (
    copy_marker_extension_sample,
    custom_extensions_dir,
    require_integration,
    run_cli_pty,
    setup_workspace,
)

pytestmark = pytest.mark.integration

_EXPECTED_DIGEST_PARTS: int = 2


def test_extension_cleans_old_digest_after_build(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    require_integration()
    workspace, env = setup_workspace(
        monkeypatch,
        tmp_path,
        "codex",
        docker_args="--env AICAGE_ENTRYPOINT_CMD=bash",
    )

    extension_dir = custom_extensions_dir() / "marker"
    extension_dir.parent.mkdir(parents=True, exist_ok=True)
    copy_marker_extension_sample(extension_dir)

    store = SettingsStore()
    project_cfg = store.load_project(workspace)
    agent_cfg = project_cfg.agents["codex"]
    agent_cfg.base = "ubuntu"
    agent_cfg.image_ref = f"{DEFAULT_EXTENDED_IMAGE_NAME}:codex-ubuntu-marker"
    agent_cfg.extensions = ["marker"]
    store.save_project(workspace, project_cfg)

    image_repository = f"{IMAGE_REGISTRY}/{IMAGE_REPOSITORY}"
    image_ref = f"{image_repository}:codex-ubuntu"
    other_ref = f"{image_repository}:gemini-ubuntu"
    subprocess.run(["docker", "pull", other_ref], check=True, capture_output=True)
    old_digest = get_local_repo_digest_for_repo(other_ref, image_repository)
    assert old_digest is not None
    subprocess.run(["docker", "tag", other_ref, image_ref], check=True, capture_output=True)
    subprocess.run(["docker", "image", "rm", other_ref], check=True, capture_output=True)
    local_digest = get_local_repo_digest_for_repo(image_ref, image_repository)
    assert local_digest == old_digest

    exit_code, output = run_cli_pty(
        ["codex", "-lc", "test -f /usr/local/share/aicage-extensions/marker.txt"],
        env=env,
        cwd=workspace,
    )
    assert exit_code == 0, output
    assert (image_repository, old_digest) not in _repo_digest_pairs()


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
