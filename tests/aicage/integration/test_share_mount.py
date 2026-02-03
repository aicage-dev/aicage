from pathlib import Path

import pytest

from aicage.paths import container_project_path

from ._helpers import require_integration, run_cli_pty, setup_workspace

pytestmark = pytest.mark.integration


def test_share_mounts_directory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    require_integration()
    workspace, env = setup_workspace(monkeypatch, tmp_path, "copilot")
    share_dir = tmp_path / "share"
    share_dir.mkdir()
    container_path = container_project_path(share_dir).as_posix()
    exit_code, output = run_cli_pty(
        [
            "--share",
            str(share_dir),
            "--env",
            "AICAGE_ENTRYPOINT_CMD=bash",
            "--",
            "copilot",
            "-lc",
            f"test -d {container_path} && touch {container_path}/ok.txt",
        ],
        env=env,
        cwd=workspace,
        input_data="\n\n\n",
    )

    assert exit_code == 0, output
    assert (share_dir / "ok.txt").exists()


def test_share_mounts_directory_read_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    require_integration()
    workspace, env = setup_workspace(monkeypatch, tmp_path, "copilot")
    share_dir = tmp_path / "share-ro"
    share_dir.mkdir()
    container_path = container_project_path(share_dir).as_posix()
    exit_code, output = run_cli_pty(
        [
            "--share",
            f"{share_dir}:ro",
            "--env",
            "AICAGE_ENTRYPOINT_CMD=bash",
            "--",
            "copilot",
            "-lc",
            f"test -d {container_path} && touch {container_path}/blocked.txt",
        ],
        env=env,
        cwd=workspace,
        input_data="\n\n\n",
    )

    assert exit_code != 0, output
    assert not (share_dir / "blocked.txt").exists()
