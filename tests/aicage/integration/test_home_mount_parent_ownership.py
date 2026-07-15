from pathlib import Path

import pytest

from ._helpers import require_integration, run_cli_pty, setup_workspace

pytestmark = pytest.mark.integration


def test_home_mount_parent_ownership_for_nested_mounts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    require_integration()
    _, env = setup_workspace(monkeypatch, tmp_path, "copilot")
    home_dir = Path(env["HOME"]).resolve()
    workspace = home_dir / "development" / "github" / "aicage" / "test"
    workspace.mkdir(parents=True, exist_ok=True)
    shared_parent = home_dir / "development" / "github"

    command = (
        "set -euo pipefail; "
        "uid=$(id -u); gid=$(id -g); "
        "test \"$(stat -c %u:%g \"$HOME\")\" = \"$uid:$gid\"; "
        "test \"$(stat -c %u:%g \"$HOME/development\")\" = \"$uid:$gid\"; "
        "mountpoint -q \"$HOME/development/github\"; "
        "test -d \"$HOME/development/github/aicage/test\""
    )
    exit_code, output = run_cli_pty(
        [
            "--menu",
            "none",
            "--share",
            str(shared_parent),
            "--env",
            "AICAGE_ENTRYPOINT_CMD=bash",
            "--",
            "copilot",
            "-lc",
            command,
        ],
        env=env,
        cwd=workspace,
    )

    assert exit_code == 0, output


def test_nested_mount_dedup_prefers_parent_mount(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    require_integration()
    _, env = setup_workspace(monkeypatch, tmp_path, "copilot")
    home_dir = Path(env["HOME"]).resolve()
    workspace = home_dir / "development" / "github" / "aicage" / "test"
    workspace.mkdir(parents=True, exist_ok=True)
    shared_parent = home_dir / "development" / "github"

    command = (
        "set -euo pipefail; "
        "parent=\"$HOME/development/github\"; "
        "child=\"$HOME/development/github/aicage/test\"; "
        "awk '{print $5}' /proc/self/mountinfo | grep -Fx \"$parent\" >/dev/null; "
        "! awk '{print $5}' /proc/self/mountinfo | grep -Fx \"$child\" >/dev/null; "
        "printf ok > \"$child/dedup-ok.txt\""
    )
    exit_code, output = run_cli_pty(
        [
            "--menu",
            "none",
            "--share",
            str(shared_parent),
            "--env",
            "AICAGE_ENTRYPOINT_CMD=bash",
            "--",
            "copilot",
            "-lc",
            command,
        ],
        env=env,
        cwd=workspace,
    )

    assert exit_code == 0, output
    assert (workspace / "dedup-ok.txt").read_text(encoding="utf-8") == "ok"


def test_workspace_path_is_usable_when_covered_by_parent_mount(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    require_integration()
    _, env = setup_workspace(monkeypatch, tmp_path, "copilot")
    home_dir = Path(env["HOME"]).resolve()
    workspace = home_dir / "development" / "github" / "aicage" / "test"
    workspace.mkdir(parents=True, exist_ok=True)
    shared_parent = home_dir / "development" / "github"

    command = (
        "set -euo pipefail; "
        "! mountpoint -q \"$AICAGE_WORKSPACE\"; "
        "mountpoint -q \"$HOME/development/github\"; "
        "test -d \"$AICAGE_WORKSPACE\"; "
        "printf keep > \"$AICAGE_WORKSPACE/workspace-owner.txt\""
    )
    exit_code, output = run_cli_pty(
        [
            "--menu",
            "none",
            "--share",
            str(shared_parent),
            "--env",
            "AICAGE_ENTRYPOINT_CMD=bash",
            "--",
            "copilot",
            "-lc",
            command,
        ],
        env=env,
        cwd=workspace,
    )

    assert exit_code == 0, output
    assert (workspace / "workspace-owner.txt").read_text(encoding="utf-8") == "keep"


def test_home_file_mount_is_direct_not_symlinked(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    require_integration()
    workspace, env = setup_workspace(monkeypatch, tmp_path, "copilot")
    home_dir = Path(env["HOME"]).resolve()
    home_file = home_dir / ".aicage-direct-file"
    home_file.write_text("direct\n", encoding="utf-8")

    command = (
        "set -euo pipefail; "
        "test -f \"$HOME/.aicage-direct-file\"; "
        "test ! -L \"$HOME/.aicage-direct-file\"; "
        "test \"$(cat \"$HOME/.aicage-direct-file\")\" = \"direct\""
    )
    exit_code, output = run_cli_pty(
        [
            "--menu",
            "none",
            "--share",
            str(home_file),
            "--env",
            "AICAGE_ENTRYPOINT_CMD=bash",
            "--",
            "copilot",
            "-lc",
            command,
        ],
        env=env,
        cwd=workspace,
    )

    assert exit_code == 0, output
