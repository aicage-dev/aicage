"""Native credential-store boundary for credential-agent secrets."""

import os
import sys

from ._base import _Keyring
from ._macos import _MacOSKeychain
from ._secret_service import _SecretService
from ._windows import _WindowsCredentialManager


def get_secret(name: str) -> str:
    return _keyring().get(name)


def set_secret(name: str, secret: str) -> None:
    _keyring().set(name, secret)


def _keyring() -> _Keyring:
    if os.name == "nt":
        return _WindowsCredentialManager()
    if sys.platform == "darwin":
        return _MacOSKeychain()
    return _SecretService()
