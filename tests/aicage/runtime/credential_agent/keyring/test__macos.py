from unittest import TestCase, mock

from aicage.runtime.credential_agent.keyring._macos import _MacOSKeychain
from aicage.runtime.credential_agent.keyring.errors import (
    KeyringError,
    SecretNotFoundError,
)


class MacOSKeychainTests(TestCase):
    def test_init_loads_security_framework(self) -> None:
        security = mock.Mock()
        with mock.patch(
            "aicage.runtime.credential_agent.keyring._macos.ctypes.CDLL",
            return_value=security,
        ):
            keychain = _MacOSKeychain()

        self.assertIs(security, keychain._security)

    def test_get_raises_for_a_missing_secret(self) -> None:
        keychain = object.__new__(_MacOSKeychain)
        keychain._security = mock.Mock()
        keychain._security.SecKeychainFindGenericPassword.return_value = (
            keychain._NOT_FOUND
        )

        with self.assertRaisesRegex(SecretNotFoundError, "No stored passphrase"):
            keychain.get("name")

    def test_set_creates_a_generic_password(self) -> None:
        keychain = object.__new__(_MacOSKeychain)
        keychain._security = mock.Mock()
        keychain._security.SecKeychainAddGenericPassword.return_value = 0
        with mock.patch.object(keychain, "get", side_effect=SecretNotFoundError):
            keychain.set("name", "secret")

        keychain._security.SecKeychainAddGenericPassword.assert_called_once()

    def test_set_replaces_an_existing_generic_password(self) -> None:
        keychain = object.__new__(_MacOSKeychain)
        keychain._security = mock.Mock()
        keychain._security.SecKeychainAddGenericPassword.return_value = 0
        with (
            mock.patch.object(keychain, "get", return_value="old"),
            mock.patch.object(keychain, "_delete") as delete,
        ):
            keychain.set("name", "secret")

        delete.assert_called_once_with("name")

    def test_set_raises_when_the_keychain_rejects_the_secret(self) -> None:
        keychain = object.__new__(_MacOSKeychain)
        keychain._security = mock.Mock()
        keychain._security.SecKeychainAddGenericPassword.return_value = -1
        with (
            mock.patch.object(keychain, "get", side_effect=SecretNotFoundError),
            self.assertRaisesRegex(KeyringError, "failed to store"),
        ):
            keychain.set("name", "secret")

    def test_get_returns_keychain_secret_and_frees_it(self) -> None:
        keychain = object.__new__(_MacOSKeychain)
        keychain._security = mock.Mock()
        keychain._security.SecKeychainFindGenericPassword.return_value = 0
        with mock.patch(
            "aicage.runtime.credential_agent.keyring._macos.ctypes.string_at",
            return_value=b"secret",
        ):
            self.assertEqual("secret", keychain.get("name"))

        keychain._security.SecKeychainItemFreeContent.assert_called_once()

    def test_get_raises_when_keychain_read_fails(self) -> None:
        keychain = object.__new__(_MacOSKeychain)
        keychain._security = mock.Mock()
        keychain._security.SecKeychainFindGenericPassword.return_value = -1

        with self.assertRaisesRegex(KeyringError, "failed to read"):
            keychain.get("name")

    def test_delete_removes_a_found_item(self) -> None:
        keychain = object.__new__(_MacOSKeychain)
        keychain._security = mock.Mock()
        keychain._security.SecKeychainFindGenericPassword.return_value = 0

        keychain._delete("name")

        keychain._security.SecKeychainItemDelete.assert_called_once()

    def test_delete_ignores_a_missing_item(self) -> None:
        keychain = object.__new__(_MacOSKeychain)
        keychain._security = mock.Mock()
        keychain._security.SecKeychainFindGenericPassword.return_value = (
            keychain._NOT_FOUND
        )

        keychain._delete("name")

        keychain._security.SecKeychainItemDelete.assert_not_called()
