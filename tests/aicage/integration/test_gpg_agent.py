import os
import shlex
import shutil
import subprocess
from pathlib import Path
from unittest import mock

import pytest

from aicage.config.config_store import SettingsStore
from aicage.config.project_config import AgentConfig, _AgentMounts
from aicage.constants import CREDENTIAL_AGENT_IMAGE
from aicage.docker.execution.env import resolve_container_user
from aicage.runtime.credential_agent import _gpg_forwarding, forwarding
from aicage.runtime.credential_agent.keyring.errors import SecretNotFoundError

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


def test_protected_gpg_key_reloads_after_restart_and_rejects_missing_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    require_integration()
    initial_cwd = Path.cwd()
    temp_root = Path(__file__).resolve().parents[4] / ".aicage-test-tmp"
    temp_root.mkdir(exist_ok=True)
    with temporary_test_root(temp_root) as root:
        home = root / "home"
        try:
            home.mkdir()
            _set_home(monkeypatch, home)
            gpg_home = home / ".gnupg"
            fingerprint = _create_gpg_sidecar_fixture(gpg_home, passphrase="secret")
            workspace = root / "workspace"
            workspace.mkdir()
            _configure_signed_git_repository(workspace, fingerprint)
            context = mock.Mock()
            context.project_cfg.path = str(workspace)
            context.project_cfg.agents = {
                "copilot": AgentConfig(mounts=_AgentMounts(gnupg=True))
            }
            keyring = {f"aicage/gpg/passphrase/{fingerprint}": "secret"}

            def get_secret(name: str) -> str:
                try:
                    return keyring[name]
                except KeyError as exc:
                    raise SecretNotFoundError() from exc

            with (
                mock.patch.object(_gpg_forwarding, "resolve_gpg_home", return_value=gpg_home),
                mock.patch.object(_gpg_forwarding, "_direct_gpg_socket", return_value=None),
                mock.patch.object(
                    _gpg_forwarding,
                    "_gpg_secret_key_fingerprints",
                    return_value=[fingerprint],
                ),
                mock.patch.object(_gpg_forwarding, "get_secret", side_effect=get_secret) as get_secret_mock,
            ):
                forwarding.ensure_gpg_setup(
                    context, "copilot", mock.Mock(), interactive=True
                )
                _assert_gpg_sidecar_key_is_protected(fingerprint)
                get_secret_mock.assert_called_once_with(
                    f"aicage/gpg/passphrase/{fingerprint}"
                )
                _assert_gpg_sidecar_client_signs(root, gpg_home, fingerprint)

                subprocess.run(
                    ["docker", "stop", "aicage-credential-agent-gpg"],
                    check=True,
                    capture_output=True,
                )
                with forwarding.forwarding(context, "copilot", mock.Mock()):
                    pass
                _assert_gpg_sidecar_client_signs(root, gpg_home, fingerprint)

                keyring.clear()
                subprocess.run(
                    ["docker", "stop", "aicage-credential-agent-gpg"],
                    check=True,
                    capture_output=True,
                )
                with pytest.raises(RuntimeError, match="Open the terminal configuration UI"):
                    with forwarding.forwarding(context, "copilot", mock.Mock()):
                        pass
        finally:
            monkeypatch.chdir(initial_cwd)


def _assert_gpg_agent_signs_commit(
    monkeypatch: pytest.MonkeyPatch,
    *,
    use_sidecar: bool,
) -> None:
    require_integration()
    initial_cwd = Path.cwd()
    temp_root = Path(__file__).resolve().parents[4] / ".aicage-test-tmp"
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

            if use_sidecar:
                fingerprint = _create_gpg_sidecar_fixture(home / ".gnupg")
                _force_gpg_sidecar(root, env, home / ".gnupg")
            else:
                fingerprint = _create_gpg_fixture(home / ".gnupg")
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
                        "&& ! find \"$GNUPGHOME/private-keys-v1.d\" -type f "
                        "-print -quit 2>/dev/null | grep -q ."
                    ),
                ],
                env=env,
                cwd=workspace,
            )

            assert exit_code == 0, output
            if use_sidecar:
                subprocess.run(
                    ["docker", "stop", "aicage-credential-agent-gpg"],
                    check=True,
                    capture_output=True,
                )
                (workspace / "signed-after-restart.txt").write_text(
                    "signed after restart\n", encoding="utf-8"
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
                        (
                            "git add signed-after-restart.txt "
                            "&& git commit -S -m signed-after-restart "
                            "&& git verify-commit HEAD "
                            "&& ! find \"$GNUPGHOME/private-keys-v1.d\" -type f "
                            "-print -quit 2>/dev/null | grep -q ."
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


def _create_gpg_sidecar_fixture(gpg_home: Path, *, passphrase: str = "") -> str:
    gpg_home.mkdir(mode=0o700)
    mount = f"type=bind,src={gpg_home},dst=/credential/gnupg"
    user = resolve_container_user()
    generate_key = (
        "gpg --batch --passphrase '' "
        "--quick-generate-key 'Aicage Integration <integration@example.com>' "
        "ed25519 sign never"
        if not passphrase
        else (
            f"printf '%s\\n' {shlex.quote(passphrase)} | "
            "gpg --batch --pinentry-mode loopback --passphrase-fd 0 "
            "--quick-generate-key 'Aicage Integration <integration@example.com>' "
            "ed25519 sign never"
        )
    )
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--user",
            user,
            "--entrypoint",
            "/bin/sh",
            "-e",
            "GNUPGHOME=/credential/gnupg",
            "--mount",
            mount,
            CREDENTIAL_AGENT_IMAGE,
            "-c",
            "chmod 700 \"$GNUPGHOME\" && "
            f"{generate_key} && gpg --batch --with-colons --list-secret-keys",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"GnuPG sidecar fixture generation failed:\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return _gpg_key_fingerprint(result.stdout)


def _assert_gpg_sidecar_key_is_protected(fingerprint: str) -> None:
    result = subprocess.run(
        [
            "docker",
            "exec",
            "aicage-credential-agent-gpg",
            "credential-agent",
            "gpg",
            "protected",
            fingerprint,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "protected"


def _assert_gpg_sidecar_client_signs(
    root: Path, gpg_home: Path, fingerprint: str
) -> None:
    client_home = root / "client-gnupg"
    shutil.rmtree(client_home, ignore_errors=True)
    client_home.mkdir(mode=0o700)
    for filename in ("pubring.kbx", "trustdb.gpg"):
        source = gpg_home / filename
        if source.is_file():
            shutil.copy2(source, client_home / filename)
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--user",
            resolve_container_user(),
            "--entrypoint",
            "/bin/sh",
            "--mount",
            "type=volume,src=aicage-credential-agent-gpg-socket,"
            "dst=/run/credential-agent,readonly",
            "--mount",
            f"type=bind,src={client_home},dst=/client-gnupg",
            CREDENTIAL_AGENT_IMAGE,
            "-c",
            "ln -s /run/credential-agent/S.gpg-agent /client-gnupg/S.gpg-agent "
            "&& printf signed > /client-gnupg/message "
            f"&& GNUPGHOME=/client-gnupg gpg --batch --local-user {fingerprint} "
            "--detach-sign /client-gnupg/message "
            "&& GNUPGHOME=/client-gnupg gpg --verify /client-gnupg/message.sig "
            "/client-gnupg/message",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert not any((client_home / "private-keys-v1.d").glob("*"))


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


def _force_gpg_sidecar(
    root: Path, env: dict[str, str], gpg_home: Path
) -> None:
    if os.name == "nt":
        return
    bin_dir = root / "bin"
    bin_dir.mkdir()
    gpgconf = bin_dir / "gpgconf"
    gpgconf.write_text(
        "#!/bin/sh\n"
        'if [ "$1 $2" = "--list-dirs homedir" ]; then\n'
        '  printf "%s\\n" "$GNUPGHOME"\n'
        "fi\n",
        encoding="utf-8",
    )
    gpgconf.chmod(0o755)
    env["GNUPGHOME"] = str(gpg_home)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"


def _gpg_command() -> list[str]:
    if os.name != "nt":
        return ["gpg"]
    gpg = Path(os.environ["ProgramFiles"]) / "Git" / "usr" / "bin" / "gpg.exe"
    if not gpg.is_file():
        raise AssertionError(f"Git for Windows did not provide gpg.exe at {gpg}.")
    return [str(gpg)]


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
