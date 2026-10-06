from pathlib import Path

import pytest

from ._helpers import build_cli_env, require_integration, run_cli_pty

pytestmark = pytest.mark.integration


def test_refuses_to_start_when_cwd_is_home(tmp_path: Path) -> None:
    require_integration()
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    env = build_cli_env(home_dir)
    env["HOME"] = str(home_dir)

    exit_code, output = run_cli_pty(
        ["--menu", "none", "codex", "--version"],
        env=env,
        cwd=home_dir,
    )

    assert exit_code == 1
    assert (
        "Refusing to start: this would expose your home directory to the container via"
        in output
    )
    assert "Use one of these safer options instead:" in output


def test_starts_when_cwd_is_home_with_opt_in(tmp_path: Path) -> None:
    require_integration()
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    env = build_cli_env(home_dir)
    env["HOME"] = str(home_dir)
    marker_path = home_dir / ".aicage-home-mount-ok"

    exit_code, output = run_cli_pty(
        [
            "--menu",
            "none",
            "--allow-home-mount",
            "--env",
            "AICAGE_ENTRYPOINT_CMD=bash",
            "--",
            "copilot",
            "-lc",
            f"test \"$HOME\" = \"{home_dir}\" && touch \"{marker_path}\"",
        ],
        env=env,
        cwd=home_dir,
    )

    assert exit_code == 0, output
    assert marker_path.exists()
