"""Windows Credential Manager backend."""

import ctypes
from ctypes import wintypes

from ._base import _Keyring
from .errors import KeyringError, SecretNotFoundError


class _WindowsCredentialManager(_Keyring):
    _TYPE_GENERIC = 1
    _PERSIST_LOCAL_MACHINE = 2
    _NOT_FOUND = 1168

    class _Credential(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD),
            ("Type", wintypes.DWORD),
            ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR),
            ("LastWritten", wintypes.FILETIME),
            ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
            ("Persist", wintypes.DWORD),
            ("AttributeCount", wintypes.DWORD),
            ("Attributes", ctypes.c_void_p),
            ("TargetAlias", wintypes.LPWSTR),
            ("UserName", wintypes.LPWSTR),
        ]

    def __init__(self) -> None:
        self._api = ctypes.WinDLL("Advapi32.dll", use_last_error=True)  # type: ignore[attr-defined]
        self._api.CredReadW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.POINTER(self._Credential)),
        ]
        self._api.CredReadW.restype = wintypes.BOOL
        self._api.CredWriteW.argtypes = [ctypes.POINTER(self._Credential), wintypes.DWORD]
        self._api.CredWriteW.restype = wintypes.BOOL
        self._api.CredFree.argtypes = [ctypes.c_void_p]
        self._api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]

    def get(self, name: str) -> str:
        credential = ctypes.POINTER(self._Credential)()
        if not self._api.CredReadW(name, self._TYPE_GENERIC, 0, ctypes.byref(credential)):
            error = ctypes.get_last_error()  # type: ignore[attr-defined]
            if error == self._NOT_FOUND:
                raise SecretNotFoundError("No stored passphrase is available.")
            raise KeyringError(f"Credential Manager failed to read the passphrase ({error}).")
        try:
            raw = ctypes.string_at(credential.contents.CredentialBlob, credential.contents.CredentialBlobSize)
            return raw.decode("utf-8")
        finally:
            self._api.CredFree(credential)

    def set(self, name: str, secret: str) -> None:
        blob = ctypes.create_string_buffer(secret.encode("utf-8"))
        credential = self._Credential(
            Type=self._TYPE_GENERIC,
            TargetName=name,
            CredentialBlobSize=len(blob.raw) - 1,
            CredentialBlob=ctypes.cast(blob, ctypes.POINTER(ctypes.c_ubyte)),
            Persist=self._PERSIST_LOCAL_MACHINE,
        )
        if not self._api.CredWriteW(ctypes.byref(credential), 0):
            error = ctypes.get_last_error()  # type: ignore[attr-defined]
            raise KeyringError(f"Credential Manager failed to store the passphrase ({error}).")
