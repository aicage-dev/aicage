import os
import re
import shlex
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from aicage.config.config_store import SettingsStore

from ._helpers import require_integration, run_cli_pty, setup_workspace

pytestmark = pytest.mark.integration

_WINDOWS_SSH_AGENT_SOCKET = r"\\.\pipe\openssh-ssh-agent"


def test_ssh_agent_is_available_in_container(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    require_integration()
    workspace, env = setup_workspace(monkeypatch, tmp_path, "copilot")
    _configure_ssh_remote(workspace)
    _enable_ssh_mount(workspace)

    with _ssh_agent(tmp_path) as (agent_env, public_key):
        env.update(agent_env)
        exit_code, output = run_cli_pty(
            [
                "--menu",
                "none",
                "-e",
                "AICAGE_ENTRYPOINT_CMD=bash",
                "--",
                "copilot",
                "-lc",
                f"ssh-add -L | grep -Fx -- {shlex.quote(public_key)}",
            ],
            env=env,
            cwd=workspace,
        )

    assert exit_code == 0, output


def _configure_ssh_remote(workspace: Path) -> None:
    subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "git@example.invalid:aicage/test.git"],
        cwd=workspace,
        check=True,
        capture_output=True,
    )


def _enable_ssh_mount(workspace: Path) -> None:
    store = SettingsStore()
    project_cfg = store.load_project(workspace)
    project_cfg.agents["copilot"].mounts.ssh = True
    store.save_project(workspace, project_cfg)


@contextmanager
def _ssh_agent(tmp_path: Path) -> Iterator[tuple[dict[str, str], str]]:
    private_key = tmp_path / "id_ed25519"
    subprocess.run(
        ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(private_key)],
        check=True,
        capture_output=True,
    )
    agent_env = _start_ssh_agent()
    command_env = {**os.environ, **agent_env}
    subprocess.run(
        ["ssh-add", str(private_key)],
        check=True,
        capture_output=True,
        env=command_env,
    )
    public_key = " ".join(
        private_key.with_suffix(".pub").read_text(encoding="utf-8").split()[:2]
    )
    try:
        yield agent_env, public_key
    finally:
        subprocess.run(
            ["ssh-add", "-d", str(private_key)],
            check=False,
            capture_output=True,
            env=command_env,
        )
        if sys.platform != "win32":
            subprocess.run(
                ["ssh-agent", "-k"],
                check=False,
                capture_output=True,
                env=command_env,
            )


def _start_ssh_agent() -> dict[str, str]:
    if sys.platform == "win32":
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "Set-Service -Name ssh-agent -StartupType Manual; Start-Service ssh-agent",
            ],
            check=True,
            capture_output=True,
        )
        return {"SSH_AUTH_SOCK": _WINDOWS_SSH_AGENT_SOCKET}

    result = subprocess.run(
        ["ssh-agent", "-s"],
        check=True,
        capture_output=True,
        text=True,
    )
    return _parse_ssh_agent_env(result.stdout)


def _parse_ssh_agent_env(output: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for name, value in re.findall(r"^(SSH_[A-Z_]+)=([^;]+);", output, re.MULTILINE):
        values[name] = value
    return values
