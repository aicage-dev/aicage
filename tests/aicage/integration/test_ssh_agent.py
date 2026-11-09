import os
import re
import shlex
import subprocess
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

import pytest

from aicage.config.config_store import SettingsStore
from aicage.config.project_config import AgentConfig, _AgentMounts
from aicage.paths import container_project_path
from aicage.runtime import _ssh_agent as ssh_agent_module
from aicage.runtime.credential_agent import _resources, _ssh_forwarding, forwarding
from aicage.runtime.credential_agent.keyring.errors import SecretNotFoundError

from ._helpers import (
    require_integration,
    run_cli_pty,
    setup_workspace,
    temporary_test_root,
)

pytestmark = pytest.mark.integration


def test_ssh_agent_is_available_in_container(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
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
            (workspace / "allowed_signers").write_text(
                f"aicage {keys.public_keys[0]}\n", encoding="utf-8"
            )
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
                        "printf '%s\\n' signed > signing-message",
                        "rm -f signing-message.sig",
                        (
                            "ssh-keygen -Y sign -U "
                            f"-f {shlex.quote(container_project_path(keys.public_paths[0]).as_posix())} "
                            "-n aicage signing-message"
                        ),
                        (
                            "ssh-keygen -Y verify -f allowed_signers -I aicage "
                            "-n aicage -s signing-message.sig < signing-message"
                        ),
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
            _assert_ssh_authentication(workspace, env, keys.public_paths[0])
            subprocess.run(
                ["docker", "stop", "aicage-credential-agent-ssh"],
                check=True,
                capture_output=True,
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
        finally:
            monkeypatch.chdir(initial_cwd)


def test_protected_ssh_key_setup_reloads_after_restart_and_rejects_missing_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    require_integration()
    initial_cwd = Path.cwd()
    temp_root = Path(__file__).resolve().parents[4] / ".aicage-test-tmp"
    temp_root.mkdir(exist_ok=True)
    with temporary_test_root(temp_root) as root:
        home = root / "home"
        home.mkdir()
        try:
            _set_home(monkeypatch, home)
            key = _configure_protected_ssh_key(home)
            context = mock.Mock()
            context.project_cfg.path = str(root / "workspace")
            context.project_cfg.agents = {
                "copilot": AgentConfig(mounts=_AgentMounts(ssh=True))
            }
            keyring: dict[str, str] = {}

            def get_secret(name: str) -> str:
                try:
                    return keyring[name]
                except KeyError as exc:
                    raise SecretNotFoundError() from exc

            with (
                _host_ssh_directory(home / ".ssh"),
                mock.patch.object(
                    _ssh_forwarding, "get_secret", side_effect=get_secret
                ),
                mock.patch.object(
                    _ssh_forwarding,
                    "set_secret",
                    side_effect=keyring.__setitem__,
                ) as set_secret,
                mock.patch.object(
                    _ssh_forwarding.sys.stdin, "isatty", return_value=True
                ),
                mock.patch.object(_ssh_forwarding, "getpass", return_value="secret"),
            ):
                forwarding.ensure_ssh_setup(
                    context, "copilot", mock.Mock(), interactive=True
                )
                set_secret.assert_called_once()
                _assert_ssh_sidecar_has_key(key)

                subprocess.run(
                    ["docker", "stop", "aicage-credential-agent-ssh"],
                    check=True,
                    capture_output=True,
                )
                with forwarding.forwarding(context, "copilot", mock.Mock()):
                    pass
                _assert_ssh_sidecar_has_key(key)

                keyring.clear()
                subprocess.run(
                    ["docker", "stop", "aicage-credential-agent-ssh"],
                    check=True,
                    capture_output=True,
                )
                with pytest.raises(
                    RuntimeError, match="Open the terminal configuration UI"
                ):
                    with forwarding.forwarding(context, "copilot", mock.Mock()):
                        pass
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
    configured_key = ssh_dir / "keys" / "work"
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


def _configure_protected_ssh_key(home: Path) -> Path:
    ssh_dir = home / ".ssh"
    ssh_dir.mkdir()
    key = ssh_dir / "id_ed25519"
    subprocess.run(
        ["ssh-keygen", "-q", "-t", "ed25519", "-N", "secret", "-f", str(key)],
        check=True,
        capture_output=True,
    )
    return key


@contextmanager
def _host_ssh_directory(ssh_dir: Path) -> Iterator[None]:
    with (
        mock.patch.object(ssh_agent_module, "HOST_SSH_DIR", ssh_dir),
        mock.patch.object(_ssh_forwarding, "HOST_SSH_DIR", ssh_dir),
        mock.patch.object(_resources, "HOST_SSH_DIR", ssh_dir),
    ):
        yield


def _assert_ssh_sidecar_has_key(key: Path) -> None:
    expected_key = " ".join(key.with_name(f"{key.name}.pub").read_text().split()[:2])
    result = subprocess.run(
        [
            "docker",
            "exec",
            "aicage-credential-agent-ssh",
            "sh",
            "-c",
            "SSH_AUTH_SOCK=/run/credential-agent/ssh-agent.sock ssh-add -L",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert expected_key in result.stdout


def _enable_ssh_mount(workspace: Path) -> None:
    store = SettingsStore()
    project_cfg = store.load_project(workspace)
    project_cfg.agents["copilot"].mounts.ssh = True
    store.save_project(workspace, project_cfg)


def _assert_ssh_authentication(
    workspace: Path, env: dict[str, str], public_key: Path
) -> None:
    image_name = "aicage-integration-sshd"
    container_name = f"aicage-integration-sshd-{uuid.uuid4().hex}"
    authorized_keys = workspace / "authorized_keys"
    store = SettingsStore()
    project_cfg = store.load_project(workspace)
    previous_docker_args = project_cfg.agents["copilot"].docker_args
    authorized_keys.write_text(public_key.read_text(encoding="utf-8"), encoding="utf-8")
    subprocess.run(
        [
            "docker",
            "build",
            "--tag",
            image_name,
            "--file",
            str(Path(__file__).with_name("sshd") / "Dockerfile"),
            str(Path(__file__).resolve().parents[3]),
        ],
        check=True,
        capture_output=True,
    )
    try:
        subprocess.run(
            [
                "docker",
                "run",
                "--detach",
                "--name",
                container_name,
                "--mount",
                f"type=bind,src={authorized_keys},dst=/authorized_keys,readonly",
                image_name,
            ],
            check=True,
            capture_output=True,
        )
        project_cfg = store.load_project(workspace)
        project_cfg.agents["copilot"].docker_args = (
            f"--network container:{container_name}"
        )
        store.save_project(workspace, project_cfg)
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
                    "ssh -F /dev/null -p 2222 -o BatchMode=yes -o PasswordAuthentication=no "
                    "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
                    "root@127.0.0.1 true"
                ),
            ],
            env=env,
            cwd=workspace,
        )
        assert exit_code == 0, output
    finally:
        project_cfg = store.load_project(workspace)
        project_cfg.agents["copilot"].docker_args = previous_docker_args
        store.save_project(workspace, project_cfg)
        subprocess.run(
            ["docker", "rm", "--force", container_name],
            check=False,
            capture_output=True,
        )


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
