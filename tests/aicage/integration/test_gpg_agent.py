import os
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from aicage.config.config_store import SettingsStore

from ._helpers import require_integration, run_cli_pty, setup_workspace

pytestmark = pytest.mark.integration


def test_gpg_agent_signs_commit_in_container(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    require_integration()
    workspace, env = setup_workspace(monkeypatch, tmp_path, "copilot")

    with _gpg_home(tmp_path) as (gpg_env, fingerprint):
        env.update(gpg_env)
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
                "git add signed.txt && git commit -S -m signed",
            ],
            env=env,
            cwd=workspace,
        )

        assert exit_code == 0, output
        subprocess.run(
            ["git", "verify-commit", "HEAD"],
            cwd=workspace,
            check=True,
            capture_output=True,
            env={**os.environ, **gpg_env},
        )


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


@contextmanager
def _gpg_home(tmp_path: Path) -> Iterator[tuple[dict[str, str], str]]:
    gpg_home = tmp_path / "gnupg"
    gpg_home.mkdir(mode=0o700)
    gpg_env = {"GNUPGHOME": str(gpg_home)}
    command_env = {**os.environ, **gpg_env}
    result = subprocess.run(
        [
            "gpg",
            "--batch",
            "--pinentry-mode",
            "loopback",
            "--passphrase",
            "",
            "--quick-generate-key",
            "Aicage Integration <integration@example.com>",
            "ed25519",
            "sign",
            "1d",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=command_env,
    )
    if result.returncode != 0:
        raise AssertionError(
            "GnuPG key generation failed:\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    try:
        yield gpg_env, _gpg_fingerprint(command_env)
    finally:
        subprocess.run(
            ["gpgconf", "--kill", "gpg-agent"],
            check=False,
            capture_output=True,
            env=command_env,
        )


def _gpg_fingerprint(env: dict[str, str]) -> str:
    result = subprocess.run(
        ["gpg", "--batch", "--with-colons", "--list-secret-keys"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    for line in result.stdout.splitlines():
        fields = line.split(":")
        if fields[0] == "fpr":
            return fields[9]
    raise AssertionError("Generated GnuPG key has no fingerprint.")
