import os
import subprocess
from pathlib import Path

import pytest

from aicage.config.config_store import SettingsStore
from aicage.constants import CREDENTIAL_AGENT_IMAGE
from aicage.docker.execution.env import resolve_container_user

from ._helpers import (
    require_integration,
    run_cli_pty,
    setup_workspace,
    temporary_test_root,
)

pytestmark = pytest.mark.integration


def test_gpg_agent_signs_commit_in_container(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    require_integration()
    initial_cwd = Path.cwd()
    temp_root = Path(__file__).resolve().parents[3] / ".aicage-test-tmp"
    temp_root.mkdir(exist_ok=True)
    with temporary_test_root(temp_root) as root:
        home = root / "home"
        try:
            home.mkdir()
            _set_home(monkeypatch, home)
            workspace, env = setup_workspace(
                monkeypatch,
                root,
                "copilot",
                workspace_path=root / "workspace",
            )

            fingerprint = _create_gpg_fixture(home / ".gnupg")
            _configure_signed_git_repository(workspace, fingerprint)
            _enable_gnupg_mount(workspace)
            (workspace / "signed.txt").write_text("signed\n", encoding="utf-8")

            exit_code, output = run_cli_pty(
                [
                    "--menu",
                    "none",
                    "-e",
                    "AICAGE_ENTRYPOINT_CMD=bash",
                    "--",
                    "copilot",
                    "-lc",
                    "git add signed.txt && git commit -S -m signed && git verify-commit HEAD",
                ],
                env=env,
                cwd=workspace,
            )

            assert exit_code == 0, output
        finally:
            monkeypatch.chdir(initial_cwd)


def _configure_signed_git_repository(workspace: Path, fingerprint: str) -> None:
    commands = (
        ["git", "init"],
        ["git", "config", "user.name", "Aicage Integration"],
        ["git", "config", "user.email", "integration@example.com"],
        ["git", "config", "commit.gpgsign", "true"],
        ["git", "config", "gpg.format", "openpgp"],
        ["git", "config", "user.signingkey", fingerprint],
    )
    for command in commands:
        subprocess.run(command, cwd=workspace, check=True, capture_output=True)


def _enable_gnupg_mount(workspace: Path) -> None:
    store = SettingsStore()
    project_cfg = store.load_project(workspace)
    project_cfg.agents["copilot"].mounts.gnupg = True
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


def _create_gpg_fixture(gpg_home: Path) -> str:
    gpg_home.mkdir(mode=0o700)
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--user",
            resolve_container_user(),
            "--entrypoint",
            "/bin/sh",
            "-e",
            "GNUPGHOME=/credential/gnupg",
            "--mount",
            f"type=bind,src={gpg_home},dst=/credential/gnupg",
            CREDENTIAL_AGENT_IMAGE,
            "-c",
            (
                "gpg --batch --passphrase '' --quick-generate-key "
                "'Aicage Integration <integration@example.com>' ed25519 sign never"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(f"GnuPG key generation failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    _remove_gpg_agent_sockets(gpg_home)
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--user",
            resolve_container_user(),
            "--entrypoint",
            "gpg",
            "-e",
            "GNUPGHOME=/credential/gnupg",
            "--mount",
            f"type=bind,src={gpg_home},dst=/credential/gnupg",
            CREDENTIAL_AGENT_IMAGE,
            "--batch",
            "--with-colons",
            "--list-secret-keys",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        fields = line.split(":")
        if fields[0] == "fpr":
            _remove_gpg_agent_sockets(gpg_home)
            return fields[9]
    raise AssertionError("Generated GnuPG key has no fingerprint.")


def _remove_gpg_agent_sockets(gpg_home: Path) -> None:
    for socket in gpg_home.glob("S.gpg-agent*"):
        socket.unlink()
