import ctypes
from unittest import TestCase, mock

from aicage.runtime.credential_agent.keyring._windows import _WindowsCredentialManager
from aicage.runtime.credential_agent.keyring.errors import KeyringError, SecretNotFoundError


class WindowsCredentialManagerTests(TestCase):
    def test_init_configures_credential_manager_functions(self) -> None:
        api = mock.Mock()
        with mock.patch.object(ctypes, "WinDLL", return_value=api, create=True):
            manager = _WindowsCredentialManager()

        self.assertIs(api, manager._api)

    def test_get_raises_for_a_missing_secret(self) -> None:
        manager = object.__new__(_WindowsCredentialManager)
        manager._api = mock.Mock()
        manager._api.CredReadW.return_value = False
        with mock.patch(
            "aicage.runtime.credential_agent.keyring._windows.ctypes.get_last_error",
            return_value=manager._NOT_FOUND,
            create=True,
        ):
            with self.assertRaisesRegex(SecretNotFoundError, "No stored passphrase"):
                manager.get("name")

    def test_set_writes_a_generic_local_machine_credential(self) -> None:
        manager = object.__new__(_WindowsCredentialManager)
        manager._api = mock.Mock()
        manager._api.CredWriteW.return_value = True

        manager.set("name", "secret")

        manager._api.CredWriteW.assert_called_once()

    def test_get_translates_unknown_read_errors(self) -> None:
        manager = object.__new__(_WindowsCredentialManager)
        manager._api = mock.Mock()
        manager._api.CredReadW.return_value = False
        with (
            mock.patch(
                "aicage.runtime.credential_agent.keyring._windows.ctypes.get_last_error",
                return_value=5,
                create=True,
            ),
            self.assertRaisesRegex(KeyringError, "failed to read the passphrase"),
        ):
            manager.get("name")

    def test_get_reads_and_frees_a_credential(self) -> None:
        manager = object.__new__(_WindowsCredentialManager)
        manager._api = mock.Mock()
        manager._api.CredReadW.return_value = True
        credential = mock.Mock()
        credential.contents.CredentialBlob = mock.sentinel.blob
        credential.contents.CredentialBlobSize = 6
        with (
            mock.patch(
                "aicage.runtime.credential_agent.keyring._windows.ctypes.POINTER", return_value=lambda: credential
            ),
            mock.patch("aicage.runtime.credential_agent.keyring._windows.ctypes.byref"),
            mock.patch("aicage.runtime.credential_agent.keyring._windows.ctypes.string_at", return_value=b"secret"),
        ):
            self.assertEqual("secret", manager.get("name"))

        manager._api.CredFree.assert_called_once_with(credential)

    def test_set_translates_write_errors(self) -> None:
        manager = object.__new__(_WindowsCredentialManager)
        manager._api = mock.Mock()
        manager._api.CredWriteW.return_value = False
        with (
            mock.patch(
                "aicage.runtime.credential_agent.keyring._windows.ctypes.get_last_error",
                return_value=5,
                create=True,
            ),
            self.assertRaisesRegex(KeyringError, "failed to store the passphrase"),
        ):
            manager.set("name", "secret")
