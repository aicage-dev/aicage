"""Host SSH agent forwarding."""

import glob
import os
import re
import shlex
import subprocess  # nosec B404 -- SSH agent management requires explicit host commands.
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from shutil import which

from aicage.paths import HOST_SSH_DIR, container_project_path
from aicage.runtime.run_args import EnvVar, MountSpec

_CONTAINER_SSH_AGENT_SOCKET = PurePosixPath("/run/aicage-ssh-agent.sock")
_SSH_AUTH_SOCK = "SSH_AUTH_SOCK"
_CONFIG_FILENAME = "config"
_KNOWN_HOST_FILENAMES = {"known_hosts", "known_hosts.old"}
_NON_KEY_FILENAMES = {
    _CONFIG_FILENAME,
    *_KNOWN_HOST_FILENAMES,
    "authorized_keys",
    "authorized_keys2",
}
_CONFIG_OPTION_VALUE_COUNT = 2
_SSH_ADD = which("ssh-add") or "ssh-add"
_SSH_AGENT = which("ssh-agent") or "ssh-agent"
_POWERSHELL = which("powershell") or "powershell"


@dataclass(frozen=True)
class _AgentConnection:
    socket: Path
    env: dict[str, str]
    temporary: bool


def _has_ssh_support() -> bool:
    return bool(_resolve_ssh_key_files()) or _resolve_ssh_agent_socket() is not None


def _resolve_ssh_key_files() -> list[Path]:
    config_files = set(_resolve_ssh_config_files())
    paths = [
        path
        for path in _ssh_directory_files()
        if path not in config_files and _is_private_key_candidate(path)
    ]
    paths.extend(_configured_private_key_files())
    return list(dict.fromkeys(paths))


def _resolve_ssh_support_files() -> list[Path]:
    paths = [*_resolve_ssh_config_files()]
    known_hosts = HOST_SSH_DIR / "known_hosts"
    if known_hosts.is_file():
        paths.append(known_hosts)
    paths.extend(_public_key_files(_resolve_ssh_key_files()))
    return list(dict.fromkeys(paths))


def _resolve_ssh_config_files() -> list[Path]:
    config = HOST_SSH_DIR / _CONFIG_FILENAME
    if not config.is_file():
        return []
    return _config_files(config, set())


@contextmanager
def forwarding(enabled: bool) -> Iterator[tuple[list[MountSpec], list[EnvVar]]]:
    if not enabled:
        yield [], []
        return

    connection = _connect_agent()
    if connection is None:
        yield [], []
        return

    added_paths = _add_keys(connection.env, _resolve_ssh_key_files())
    mounts = [
        MountSpec(
            host_path=connection.socket,
            container_path=_CONTAINER_SSH_AGENT_SOCKET,
        ),
        *[
            MountSpec(
                host_path=path,
                container_path=container_project_path(path),
                read_only=True,
            )
            for path in _resolve_ssh_support_files()
        ],
    ]
    env = [EnvVar(name=_SSH_AUTH_SOCK, value=_CONTAINER_SSH_AGENT_SOCKET.as_posix())]
    try:
        yield mounts, env
    finally:
        _remove_keys(connection.env, added_paths)
        if connection.temporary:
            _stop_agent(connection.env)


def _ssh_directory_files() -> list[Path]:
    if not HOST_SSH_DIR.is_dir():
        return []
    return [path for path in HOST_SSH_DIR.rglob("*") if path.is_file()]


def _is_private_key_candidate(path: Path) -> bool:
    return path.name not in _NON_KEY_FILENAMES and path.suffix != ".pub"


def _configured_private_key_files() -> list[Path]:
    paths: list[Path] = []
    for config in _resolve_ssh_config_files():
        for value in _config_values(config, "IdentityFile"):
            if "%" in value:
                continue
            path = Path(value).expanduser()
            if path.suffix == ".pub":
                path = path.with_suffix("")
            if path.is_file():
                paths.append(path)
    return paths


def _config_files(config: Path, seen: set[Path]) -> list[Path]:
    resolved = config.resolve()
    if resolved in seen:
        return []
    seen.add(resolved)
    paths = [config]
    for value in _config_values(config, "Include"):
        pattern = Path(value).expanduser()
        if not pattern.is_absolute():
            pattern = config.parent / pattern
        for match in glob.glob(str(pattern)):
            child = Path(match)
            if child.is_file():
                paths.extend(_config_files(child, seen))
    return paths


def _config_values(config: Path, option: str) -> list[str]:
    values: list[str] = []
    for line in config.read_text(encoding="utf-8").splitlines():
        tokens = shlex.split(line, comments=True, posix=os.name != "nt")
        if (
            len(tokens) >= _CONFIG_OPTION_VALUE_COUNT
            and tokens[0].lower() == option.lower()
        ):
            values.append(tokens[1])
    return values


def _public_key_files(private_keys: list[Path]) -> list[Path]:
    return [
        public_key
        for private_key in private_keys
        if (public_key := private_key.with_name(f"{private_key.name}.pub")).is_file()
    ]


def _connect_agent() -> _AgentConnection | None:
    socket = _resolve_ssh_agent_socket()
    if socket is not None:
        env = {**os.environ, _SSH_AUTH_SOCK: str(socket)}
        if _agent_is_reachable(env):
            return _AgentConnection(socket=socket, env=env, temporary=False)
    if os.name == "nt":
        return _start_windows_agent()
    return _start_unix_agent()


def _agent_is_reachable(env: dict[str, str]) -> bool:
    result = subprocess.run(  # nosec B603 -- fixed ssh-add probe.
        [_SSH_ADD, "-l"], env=env, check=False, capture_output=True, text=True
    )
    return result.returncode in {0, 1}


def _start_unix_agent() -> _AgentConnection | None:
    result = subprocess.run(  # nosec B603 -- fixed ssh-agent command.
        [_SSH_AGENT, "-s"], check=False, capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    values = dict(re.findall(r"^(SSH_[A-Z_]+)=([^;]+);", result.stdout, re.MULTILINE))
    socket_value = values.get(_SSH_AUTH_SOCK)
    if not socket_value:
        return None
    env = {**os.environ, **values}
    return _AgentConnection(socket=Path(socket_value), env=env, temporary=True)


def _start_windows_agent() -> _AgentConnection | None:
    subprocess.run(  # nosec B603 -- fixed PowerShell service command.
        [
            _POWERSHELL,
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "Set-Service -Name ssh-agent -StartupType Manual; Start-Service ssh-agent",
        ],
        check=False,
    )
    socket = _resolve_ssh_agent_socket()
    if socket is None:
        return None
    env = {**os.environ, _SSH_AUTH_SOCK: str(socket)}
    return _AgentConnection(socket=socket, env=env, temporary=False)


def _add_keys(env: dict[str, str], paths: list[Path]) -> list[Path]:
    added: list[Path] = []
    for path in paths:
        result = subprocess.run(  # nosec B603 -- paths are discovered from host SSH configuration.
            [_SSH_ADD, str(path)], env=env, check=False
        )
        if result.returncode == 0:
            added.append(path)
    return added


def _remove_keys(env: dict[str, str], paths: list[Path]) -> None:
    for path in paths:
        subprocess.run(  # nosec B603 -- paths were added by this process.
            [_SSH_ADD, "-d", str(path)], env=env, check=False, capture_output=True
        )


def _stop_agent(env: dict[str, str]) -> None:
    subprocess.run(  # nosec B603 -- fixed ssh-agent cleanup command.
        [_SSH_AGENT, "-k"], env=env, check=False, capture_output=True
    )


def _resolve_ssh_agent_socket() -> Path | None:
    socket_path = os.environ.get(_SSH_AUTH_SOCK)
    if socket_path:
        return Path(socket_path)
    if os.name == "nt":
        return Path(r"\\.\pipe\openssh-ssh-agent")
    return None
