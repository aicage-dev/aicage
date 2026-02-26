from pathlib import Path

import pytest

from .._helpers import (
    custom_agents_dir,
    require_integration,
    run_cli_pty,
    setup_custom_bash_agent,
    setup_workspace,
)

pytestmark = pytest.mark.integration

_AGENT_NAME: str = "bash"


def test_agent_path_files_and_directories_create_and_mount(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    require_integration()
    workspace, env = setup_workspace(monkeypatch, tmp_path, _AGENT_NAME)
    agent_dir = custom_agents_dir() / _AGENT_NAME
    setup_custom_bash_agent(agent_dir)

    exit_code, output = run_cli_pty(
        [
            "--",
            "bash",
            "-lc",
            "test -d ~/.aicage-test-dir "
            "&& test -f ~/.aicage-test-file "
            "&& test -f ~/.aicage-test-file.backup",
        ],
        env=env,
        cwd=workspace,
        input_data="\n\n\n",
    )

    assert exit_code == 0, output
