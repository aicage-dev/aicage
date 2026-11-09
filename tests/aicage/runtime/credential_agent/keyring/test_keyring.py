from unittest import TestCase, mock

from aicage.runtime.credential_agent.keyring import keyring


class KeyringTests(TestCase):
    def test_keyring_selects_each_platform_backend(self) -> None:
        windows = mock.Mock()
        with (
            mock.patch.object(keyring.os, "name", "nt"),
            mock.patch.object(
                keyring, "_WindowsCredentialManager", return_value=windows
            ),
        ):
            self.assertIs(windows, keyring._keyring())
        macos = mock.Mock()
        with (
            mock.patch.object(keyring.os, "name", "posix"),
            mock.patch.object(keyring.sys, "platform", "darwin"),
            mock.patch.object(keyring, "_MacOSKeychain", return_value=macos),
        ):
            self.assertIs(macos, keyring._keyring())

    def test_get_secret_delegates_to_platform_keyring(self) -> None:
        backend = mock.Mock()
        backend.get.return_value = "secret"
        with mock.patch.object(keyring, "_keyring", return_value=backend):
            actual = keyring.get_secret("aicage/ssh/passphrase/SHA256:key")

        self.assertEqual("secret", actual)
        backend.get.assert_called_once_with("aicage/ssh/passphrase/SHA256:key")

    def test_set_secret_delegates_to_platform_keyring(self) -> None:
        backend = mock.Mock()
        with mock.patch.object(keyring, "_keyring", return_value=backend):
            keyring.set_secret("aicage/ssh/passphrase/SHA256:key", "secret")

        backend.set.assert_called_once_with(
            "aicage/ssh/passphrase/SHA256:key", "secret"
        )
