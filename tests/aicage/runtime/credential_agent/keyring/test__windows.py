import ctypes
from unittest import TestCase, mock

from aicage.runtime.credential_agent.keyring._windows import _WindowsCredentialManager
from aicage.runtime.credential_agent.keyring.errors import SecretNotFoundError


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
