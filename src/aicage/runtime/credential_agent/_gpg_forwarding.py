"""GnuPG credential-forwarding operations."""

import os
import subprocess  # nosec B404 -- GnuPG readiness uses a fixed host command.
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from getpass import getpass
from pathlib import Path, PurePosixPath
from shutil import copy2, which

from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig
from aicage.paths import container_project_path
from aicage.runtime.docker_args.support.git_support import (
    resolve_gpg_agent_socket,
    resolve_gpg_home,
    resolve_gpg_public_files,
)
from aicage.runtime.docker_args.support.signing import (
    is_commit_signing_enabled,
    resolve_signing_format,
)
from aicage.runtime.run_args import BindMountSpec, EnvVar, MountSpec, VolumeMountSpec

from ._resource_gpg import _gpg_key_is_protected, _load_gpg_key
from ._resource_models import _CredentialProtocol, _CredentialResource
from .keyring.errors import KeyringError, SecretNotFoundError
from .keyring.keyring import get_secret, set_secret

_GNUPGHOME = "GNUPGHOME"
_GPG_SOCKET_NAME = "S.gpg-agent"
_GPG_CONNECT_AGENT = which("gpg-connect-agent")
_GPG = which("gpg")
_GIT = which("git")
_GPG_CLIENT_HOME = PurePosixPath("/run/credential-agent-client/gnupg")
_GPG_FINGERPRINT_FIELD = 9


@dataclass
class _GpgForwardingPlan:
    credential_home: Path
    target_mounts: list[BindMountSpec]
    target_env: list[EnvVar]
    requires_sidecar: bool

    @contextmanager
    def sidecar_target_args(
        self, resource: _CredentialResource
    ) -> Iterator[tuple[list[MountSpec], list[EnvVar]]]:
        with _gpg_sidecar_target_args(resource, self.credential_home) as args:
            yield args


def _gpg_enabled(context: ConfigContext, agent: str) -> bool:
    agent_cfg = context.project_cfg.agents.get(agent, AgentConfig())
    project_path = Path(context.project_cfg.path)
    return (
        agent_cfg.mounts.gnupg is True
        and is_commit_signing_enabled(project_path)
        and resolve_signing_format(project_path) != "ssh"
    )


def _gpg_forwarding() -> _GpgForwardingPlan | None:
    gpg_home = resolve_gpg_home()
    if gpg_home is None:
        return None
    container_home = container_project_path(gpg_home)
    socket = _direct_gpg_socket()
    if socket is not None:
        return _GpgForwardingPlan(
            gpg_home,
            [
                BindMountSpec(socket, container_home / _GPG_SOCKET_NAME),
                *_gpg_support_mounts(gpg_home),
            ],
            [EnvVar(_GNUPGHOME, container_home.as_posix())],
            False,
        )
    return _GpgForwardingPlan(gpg_home, [], [], True)


def _reload_gpg_keys(
    resources: list[_CredentialResource],
    project_path: Path,
    gpg_home: Path,
    *,
    interactive: bool,
) -> None:
    resource = next(
        (item for item in resources if item.protocol is _CredentialProtocol.GPG), None
    )
    if resource is None:
        return
    for fingerprint in _gpg_secret_key_fingerprints(project_path):
        if _gpg_key_is_protected(resource, fingerprint):
            _load_gpg_key(
                resource,
                fingerprint,
                _gpg_passphrase(fingerprint, interactive=interactive),
            )


def _gpg_secret_key_fingerprints(project_path: Path) -> list[str]:
    signing_key = _gpg_signing_key(project_path)
    command = [
        _gpg(),
        "--batch",
        "--with-colons",
        "--list-secret-keys",
    ]
    if signing_key and signing_key.strip():
        command.append(signing_key.strip())
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )  # nosec B603 -- command is a fixed local GnuPG invocation.
    if result.returncode != 0:
        raise RuntimeError("Cannot inspect GnuPG secret keys for commit signing.")
    return _primary_gpg_fingerprints(result.stdout)


def _gpg_signing_key(project_path: Path) -> str | None:
    result = subprocess.run(
        [_git(), "config", "--get", "user.signingkey"],
        check=False,
        capture_output=True,
        text=True,
        cwd=project_path,
    )  # nosec B603 -- command is a fixed local Git invocation.
    return result.stdout if result.returncode == 0 else None


def _primary_gpg_fingerprints(output: str) -> list[str]:
    fingerprints: list[str] = []
    secret_key_pending = False
    for line in output.splitlines():
        fields = line.split(":")
        record_type = fields[0]
        if record_type == "sec":
            secret_key_pending = True
            continue
        if (
            record_type == "fpr"
            and secret_key_pending
            and len(fields) > _GPG_FINGERPRINT_FIELD
        ):
            fingerprints.append(fields[_GPG_FINGERPRINT_FIELD])
            secret_key_pending = False
            continue
        if record_type in {"sec", "ssb"}:
            secret_key_pending = False
    return fingerprints[:1]


def _gpg_passphrase(fingerprint: str, *, interactive: bool) -> str:
    secret_name = f"aicage/gpg/passphrase/{fingerprint}"
    try:
        return get_secret(secret_name)
    except SecretNotFoundError:
        if not interactive or not sys.stdin.isatty():
            raise RuntimeError(
                "No passphrase for GnuPG signing key "
                f"'{fingerprint}' is stored in the platform keyring. "
                "Open the terminal configuration UI to add this key."
            ) from None
        passphrase = getpass(f"Passphrase for GnuPG signing key {fingerprint}: ")
        if not passphrase:
            raise RuntimeError(
                f"No passphrase was supplied for GnuPG signing key '{fingerprint}'."
            ) from None
        set_secret(secret_name, passphrase)
        return passphrase
    except KeyringError as exc:
        raise RuntimeError(
            f"Cannot access the platform keyring for GnuPG signing key '{fingerprint}'."
        ) from exc


def _gpg() -> str:
    if _GPG is None:
        raise RuntimeError("gpg is required to inspect GnuPG signing keys.")
    return _GPG


def _git() -> str:
    if _GIT is None:
        raise RuntimeError("git is required to inspect GnuPG signing keys.")
    return _GIT


@contextmanager
def _gpg_sidecar_target_args(
    resource: _CredentialResource,
    gpg_home: Path,
) -> Iterator[tuple[list[MountSpec], list[EnvVar]]]:
    with tempfile.TemporaryDirectory(
        dir=gpg_home.parent, prefix=".aicage-gpg-"
    ) as directory:
        client_home = Path(directory)
        _copy_gpg_support_files(gpg_home, client_home)
        (client_home / _GPG_SOCKET_NAME).symlink_to(resource.socket_path)
        yield (
            [
                BindMountSpec(client_home, _GPG_CLIENT_HOME),
                *_external_gpg_support_mounts(gpg_home),
                VolumeMountSpec(
                    resource.volume_name, resource.socket_directory, True
                ),
            ],
            [EnvVar(_GNUPGHOME, _GPG_CLIENT_HOME.as_posix())],
        )


def _gpg_support_mounts(gpg_home: Path) -> list[BindMountSpec]:
    return [
        BindMountSpec(path, container_project_path(path), True)
        for path in resolve_gpg_public_files(gpg_home)
    ]


def _copy_gpg_support_files(gpg_home: Path, client_home: Path) -> None:
    for path in resolve_gpg_public_files(gpg_home):
        try:
            relative_path = path.relative_to(gpg_home)
        except ValueError:
            continue
        destination = client_home / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        copy2(path, destination)


def _external_gpg_support_mounts(gpg_home: Path) -> list[BindMountSpec]:
    return [
        BindMountSpec(path, container_project_path(path), True)
        for path in resolve_gpg_public_files(gpg_home)
        if not path.is_relative_to(gpg_home)
    ]


def _direct_gpg_socket() -> Path | None:
    if os.name == "nt":
        return None
    socket = resolve_gpg_agent_socket()
    if socket is None or _GPG_CONNECT_AGENT is None or not socket.is_socket():
        return None
    result = subprocess.run(
        [_GPG_CONNECT_AGENT, "--raw-socket", str(socket), "/bye"],
        check=False,
        capture_output=True,
        text=True,
    )  # nosec B603
    return socket if result.returncode == 0 else None
