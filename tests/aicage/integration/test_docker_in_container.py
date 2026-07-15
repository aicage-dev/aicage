from pathlib import Path

import pytest

from ._helpers import require_integration, run_cli_pty, setup_workspace

pytestmark = pytest.mark.integration


def test_docker_socket_runs_hello_world_in_container(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    require_integration()
    workspace, env = setup_workspace(monkeypatch, tmp_path, "codex")

    exit_code, output = run_cli_pty(
        [
            "--menu",
            "none",
            "--docker",
            "-e",
            "AICAGE_ENTRYPOINT_CMD=bash",
            "--",
            "codex",
            "-lc",
            "docker run --rm hello-world",
        ],
        env=env,
        cwd=workspace,
    )

    assert exit_code == 0, output
    assert "Hello from Docker!" in output
