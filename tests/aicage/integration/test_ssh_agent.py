import os
import re
import shlex
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from aicage.config.config_store import SettingsStore
from aicage.paths import container_project_path

from ._helpers import require_integration, run_cli_pty, setup_workspace

pytestmark = pytest.mark.integration


def test_ssh_agent_is_available_in_container(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    require_integration()
    initial_cwd = Path.cwd()
    temp_root = Path(__file__).resolve().parents[3] / ".aicage-test-tmp"
    temp_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=temp_root) as temp_dir:
        root = Path(temp_dir)
        home = root / "home"
        try:
            home.mkdir()
            _set_home(monkeypatch, home)
            workspace, env = setup_workspace(
                monkeypatch,
                tmp_path,
                "copilot",
                workspace_path=root / "workspace",
            )
            subprocess.run(
                ["git", "init", "--quiet"],
                cwd=workspace,
                check=True,
                capture_output=True,
            )
            keys = _configure_ssh_keys(home)
            _enable_ssh_mount(workspace)

            with _ssh_agent(root / "agent.sock") as agent_env:
                subprocess.run(
                    ["ssh-add", *(str(key) for key in keys.private_paths)],
                    check=True,
                    capture_output=True,
                    env={**os.environ, **agent_env},
                )
                env.update(agent_env)
                command = " && ".join(
                    [
                        *[
                            f"ssh-add -L | grep -F -- {shlex.quote(public_key)}"
                            for public_key in keys.public_keys
                        ],
                        *[
                            f"test -r {shlex.quote(container_project_path(path).as_posix())}"
                            for path in keys.public_paths
                        ],
                        *[
                            f"! test -e {shlex.quote(container_project_path(path).as_posix())}"
                            for path in keys.private_paths
                        ],
                    ]
                )
                exit_code, output = run_cli_pty(
                    [
                        "--menu",
                        "none",
                        "-e",
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
        except Exception:
            # TEST-WIP(Task 42): retain Aicage logs for the CI failure artifact.
            aicage_home = home / ".aicage"
            if aicage_home.is_dir():
                shutil.copytree(
                    aicage_home, temp_root / f"failed-{root.name}" / ".aicage"
                )
            raise
        finally:
            monkeypatch.chdir(initial_cwd)


class _SshKeys:
    def __init__(self, private_paths: list[Path]) -> None:
        self.private_paths = private_paths
        self.public_paths = [
            path.with_name(f"{path.name}.pub") for path in private_paths
        ]
        self.public_keys = [
            " ".join(path.read_text(encoding="utf-8").split()[:2])
            for path in self.public_paths
        ]


def _configure_ssh_keys(home: Path) -> _SshKeys:
    ssh_dir = home / ".ssh"
    ssh_dir.mkdir()
    default_key = ssh_dir / "id_ed25519"
    configured_key = home / "keys" / "work"
    configured_key.parent.mkdir()
    for key in (default_key, configured_key):
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)],
            check=True,
            capture_output=True,
        )
    included_config = ssh_dir / "config.d" / "work"
    included_config.parent.mkdir()
    included_config.write_text(
        f"Host work.example\n    IdentityFile {configured_key}\n",
        encoding="utf-8",
    )
    (ssh_dir / "config").write_text("Include config.d/*\n", encoding="utf-8")
    return _SshKeys([default_key, configured_key])


def _enable_ssh_mount(workspace: Path) -> None:
    store = SettingsStore()
    project_cfg = store.load_project(workspace)
    project_cfg.agents["copilot"].mounts.ssh = True
    store.save_project(workspace, project_cfg)


def _set_home(monkeypatch: pytest.MonkeyPatch, home: Path) -> None:
    home_str = str(home)
    monkeypatch.setenv("HOME", home_str)
    if os.name == "nt":
        drive, tail = os.path.splitdrive(home_str)
        monkeypatch.setenv("USERPROFILE", home_str)
        if drive:
            monkeypatch.setenv("HOMEDRIVE", drive)
            monkeypatch.setenv("HOMEPATH", tail or "\\")


@contextmanager
def _ssh_agent(socket: Path) -> Iterator[dict[str, str]]:
    result = subprocess.run(
        ["ssh-agent", "-a", str(socket), "-s"],
        check=True,
        capture_output=True,
        text=True,
    )
    agent_env = dict(
        re.findall(r"^(SSH_[A-Z_]+)=([^;]+);", result.stdout, re.MULTILINE)
    )
    try:
        yield agent_env
    finally:
        subprocess.run(
            ["ssh-agent", "-k"],
            check=False,
            capture_output=True,
            env={**os.environ, **agent_env},
        )
