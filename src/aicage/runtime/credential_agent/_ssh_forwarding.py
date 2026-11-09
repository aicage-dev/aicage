"""SSH credential-forwarding operations."""

import subprocess  # nosec B404 -- SSH key inspection uses fixed local commands.
import sys
from getpass import getpass
from pathlib import Path, PurePosixPath
from shutil import which

from aicage.paths import HOST_SSH_DIR, container_project_path
from aicage.runtime._ssh_agent import (
    _resolve_ssh_key_files,
    _resolve_ssh_support_files,
)
from aicage.runtime.run_args import BindMountSpec, EnvVar, MountSpec, VolumeMountSpec

from ._resource_models import _CredentialProtocol, _CredentialResource
from ._resource_ssh import _load_ssh_key
from .keyring.errors import KeyringError, SecretNotFoundError
from .keyring.keyring import get_secret, set_secret

_SSH_AUTH_SOCK = "SSH_AUTH_SOCK"
_SSH_SOCKET_DIRECTORY = PurePosixPath("/run/credential-agent")
_SSH_SOCKET = _SSH_SOCKET_DIRECTORY / "ssh-agent.sock"
_SSH_FINGERPRINT_FIELD = 1
_SSH_FINGERPRINT_FIELD_COUNT = 2
_SSH_KEYGEN = which("ssh-keygen")


def _ssh_forwarding() -> tuple[list[BindMountSpec], list[EnvVar], bool]:
    support_mounts = _ssh_support_mounts()
    if not _resolve_ssh_key_files() and not HOST_SSH_DIR.is_dir():
        return support_mounts, [], False
    return support_mounts, [], True


def _append_ssh_target_args(
    resource: _CredentialResource,
    mounts: list[MountSpec],
    env: list[EnvVar],
) -> None:
    mounts.append(VolumeMountSpec(resource.volume_name, _SSH_SOCKET_DIRECTORY, True))
    env.append(EnvVar(_SSH_AUTH_SOCK, _SSH_SOCKET.as_posix()))


def _ssh_support_mounts() -> list[BindMountSpec]:
    return [
        BindMountSpec(path, container_project_path(path), True)
        for path in _resolve_ssh_support_files()
    ]


def _reload_ssh_keys(
    resources: list[_CredentialResource], *, interactive: bool
) -> None:
    resource = next(
        (item for item in resources if item.protocol is _CredentialProtocol.SSH), None
    )
    if resource is None:
        return
    for key in _resolve_ssh_key_files():
        try:
            relative_key = key.relative_to(HOST_SSH_DIR)
        except ValueError as exc:
            raise RuntimeError(
                f"SSH key '{key}' is outside {HOST_SSH_DIR} and cannot be shared safely."
            ) from exc
        _load_ssh_key(
            resource,
            resource.credential_directory / relative_key,
            _ssh_passphrase(key, interactive=interactive),
        )


def _ssh_passphrase(key: Path, *, interactive: bool) -> str:
    if not _ssh_key_is_encrypted(key):
        return ""
    secret_name = f"aicage/ssh/passphrase/{_ssh_key_fingerprint(key)}"
    try:
        return get_secret(secret_name)
    except SecretNotFoundError:
        if not interactive or not sys.stdin.isatty():
            raise RuntimeError(
                f"No passphrase for SSH key '{key.name}' is stored in the platform keyring. "
                "Open the terminal configuration UI to add this key."
            ) from None
        passphrase = getpass(f"Passphrase for SSH key {key.name}: ")
        if not passphrase:
            raise RuntimeError(
                f"No passphrase was supplied for SSH key '{key.name}'."
            ) from None
        set_secret(secret_name, passphrase)
        return passphrase
    except KeyringError as exc:
        raise RuntimeError(
            f"Cannot access the platform keyring for SSH key '{key.name}'."
        ) from exc


def _ssh_key_is_encrypted(key: Path) -> bool:
    result = subprocess.run(  # nosec B603 -- fixed local key inspection.
        [_ssh_keygen(), "-y", "-P", "", "-f", str(key)],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode != 0


def _ssh_key_fingerprint(key: Path) -> str:
    public_key = key.with_name(f"{key.name}.pub")
    result = subprocess.run(
        [
            _ssh_keygen(),
            "-lf",
            str(public_key if public_key.is_file() else key),
            "-E",
            "sha256",
        ],
        check=False,
        capture_output=True,
        text=True,
    )  # nosec B603
    fields = result.stdout.split()
    if (
        result.returncode != 0
        or len(fields) < _SSH_FINGERPRINT_FIELD_COUNT
        or not fields[_SSH_FINGERPRINT_FIELD].startswith("SHA256:")
    ):
        raise RuntimeError(
            f"Cannot determine the fingerprint for SSH key '{key.name}'."
        )
    return fields[_SSH_FINGERPRINT_FIELD]


def _ssh_keygen() -> str:
    if _SSH_KEYGEN is None:
        raise RuntimeError("ssh-keygen is required to inspect SSH keys.")
    return _SSH_KEYGEN
