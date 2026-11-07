"""macOS Keychain backend."""

import ctypes

from ._base import _Keyring
from .errors import KeyringError, SecretNotFoundError


class _MacOSKeychain(_Keyring):
    _NOT_FOUND = -25300

    def __init__(self) -> None:
        self._security = ctypes.CDLL(
            "/System/Library/Frameworks/Security.framework/Security"
        )

    def get(self, name: str) -> str:
        password_length = ctypes.c_uint32()
        password = ctypes.c_void_p()
        item = ctypes.c_void_p()
        status = self._security.SecKeychainFindGenericPassword(
            None,
            len(b"aicage"),
            b"aicage",
            len(name.encode()),
            name.encode(),
            ctypes.byref(password_length),
            ctypes.byref(password),
            ctypes.byref(item),
        )
        if status == self._NOT_FOUND:
            raise SecretNotFoundError("No stored passphrase is available.")
        if status != 0:
            raise KeyringError(f"Keychain failed to read the passphrase ({status}).")
        try:
            return ctypes.string_at(password, password_length.value).decode("utf-8")
        finally:
            self._security.SecKeychainItemFreeContent(None, password)

    def set(self, name: str, secret: str) -> None:
        encoded_name, encoded_secret = name.encode(), secret.encode()
        try:
            self.get(name)
        except SecretNotFoundError:
            pass
        else:
            self._delete(name)
        status = self._security.SecKeychainAddGenericPassword(
            None,
            len(b"aicage"),
            b"aicage",
            len(encoded_name),
            encoded_name,
            len(encoded_secret),
            encoded_secret,
            None,
        )
        if status != 0:
            raise KeyringError(f"Keychain failed to store the passphrase ({status}).")

    def _delete(self, name: str) -> None:
        item = ctypes.c_void_p()
        status = self._security.SecKeychainFindGenericPassword(
            None,
            len(b"aicage"),
            b"aicage",
            len(name.encode()),
            name.encode(),
            None,
            None,
            ctypes.byref(item),
        )
        if status == 0:
            self._security.SecKeychainItemDelete(item)
