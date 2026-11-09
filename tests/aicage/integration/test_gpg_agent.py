import os
import subprocess
from pathlib import Path

import pytest

from aicage.config.config_store import SettingsStore

from ._helpers import (
    require_integration,
    run_cli_pty,
    setup_workspace,
    temporary_test_root,
)

pytestmark = pytest.mark.integration


def test_gpg_agent_signs_commit_through_direct_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.name == "nt":
        pytest.skip("Windows always uses the GnuPG credential sidecar.")
    _assert_gpg_agent_signs_commit(monkeypatch, use_sidecar=False)


def test_gpg_agent_signs_commit_through_sidecar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _assert_gpg_agent_signs_commit(monkeypatch, use_sidecar=True)


def _assert_gpg_agent_signs_commit(
    monkeypatch: pytest.MonkeyPatch,
    *,
    use_sidecar: bool,
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
            if use_sidecar:
                _stop_host_gpg_agent(home / ".gnupg")
            else:
                _prime_host_gpg_agent(home / ".gnupg", fingerprint)
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
                    (
                        "git add signed.txt && git commit -S -m signed "
                        "&& git verify-commit HEAD "
                        "&& ! gpg --batch --with-colons --list-secret-keys "
                        "| grep -qE '^(sec|ssb):'"
                    ),
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
    monkeypatch.setenv("GNUPGHOME", str(home / ".gnupg"))
    if os.name == "nt":
        drive, tail = os.path.splitdrive(home_str)
        monkeypatch.setenv("USERPROFILE", home_str)
        if drive:
            monkeypatch.setenv("HOMEDRIVE", drive)
            monkeypatch.setenv("HOMEPATH", tail or "\\")


def _create_gpg_fixture(gpg_home: Path) -> str:
    gpg_home.mkdir(mode=0o700)
    _create_gpg_fixture_on_host(gpg_home)
    result = _list_gpg_secret_keys_on_host(gpg_home)
    return _gpg_key_fingerprint(result.stdout)


def _create_gpg_fixture_on_host(gpg_home: Path) -> None:
    result = subprocess.run(
        [
            *_gpg_command(),
            "--batch",
            "--passphrase",
            "",
            "--quick-generate-key",
            "Aicage Integration <integration@example.com>",
            "ed25519",
            "sign",
            "never",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=_gpg_environment(gpg_home),
    )
    if result.returncode != 0:
        raise AssertionError(f"GnuPG key generation failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")


def _list_gpg_secret_keys_on_host(gpg_home: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*_gpg_command(), "--batch", "--with-colons", "--list-secret-keys"],
        check=True,
        capture_output=True,
        text=True,
        env=_gpg_environment(gpg_home),
    )


def _gpg_key_fingerprint(stdout: str) -> str:
    for line in stdout.splitlines():
        fields = line.split(":")
        if fields[0] == "fpr":
            return fields[9]
    raise AssertionError("Generated GnuPG key has no fingerprint.")


def _prime_host_gpg_agent(gpg_home: Path, fingerprint: str) -> None:
    env = _gpg_environment(gpg_home)
    result = subprocess.run(
        [*_gpg_command(), "--batch", "--with-colons", "--list-secret-keys"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    if fingerprint not in result.stdout:
        raise AssertionError("Host GnuPG did not find the generated secret key.")


def _stop_host_gpg_agent(gpg_home: Path) -> None:
    subprocess.run(
        [*_gpgconf_command(), "--kill", "gpg-agent"],
        check=True,
        capture_output=True,
        env=_gpg_environment(gpg_home),
    )


def _gpg_command() -> list[str]:
    if os.name != "nt":
        return ["gpg"]
    gpg = Path(os.environ["ProgramFiles"]) / "Git" / "usr" / "bin" / "gpg.exe"
    if not gpg.is_file():
        raise AssertionError(f"Git for Windows did not provide gpg.exe at {gpg}.")
    return [str(gpg)]


def _gpgconf_command() -> list[str]:
    if os.name != "nt":
        return ["gpgconf"]
    gpg = Path(_gpg_command()[0])
    return [str(gpg.with_name("gpgconf.exe"))]


def _gpg_environment(gpg_home: Path) -> dict[str, str]:
    env = {**os.environ, "GNUPGHOME": str(gpg_home)}
    if os.name == "nt":
        result = subprocess.run(
            ["cygpath", "--unix", str(gpg_home)],
            check=True,
            capture_output=True,
            text=True,
        )
        env["GNUPGHOME"] = result.stdout.strip()
    return env
