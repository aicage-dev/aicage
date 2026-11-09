import sys
from unittest import TestCase, mock

from aicage.runtime.credential_agent.keyring._secret_service import _SecretService
from aicage.runtime.credential_agent.keyring.errors import KeyringError


class SecretServiceTests(TestCase):
    def test_init_connects_to_the_default_collection(self) -> None:
        secretstorage = mock.Mock()
        collection = mock.Mock()
        secretstorage.get_default_collection.return_value = collection
        with mock.patch.dict(sys.modules, {"secretstorage": secretstorage}):
            service = _SecretService()

        self.assertIs(collection, service._collection)

    def test_get_returns_matching_unlocked_secret(self) -> None:
        item = mock.Mock()
        item.is_locked.return_value = False
        item.get_secret.return_value = b"secret"
        collection = mock.Mock()
        collection.is_locked.return_value = False
        collection.search_items.return_value = iter([item])
        service = object.__new__(_SecretService)
        service._collection = collection

        actual = service.get("name")

        self.assertEqual("secret", actual)
        collection.search_items.assert_called_once_with({"aicage.credential": "name"})

    def test_set_creates_or_replaces_secret(self) -> None:
        collection = mock.Mock()
        collection.is_locked.return_value = False
        service = object.__new__(_SecretService)
        service._collection = collection

        service.set("name", "secret")

        collection.create_item.assert_called_once_with(
            "Aicage credential name",
            {"aicage.credential": "name"},
            b"secret",
            replace=True,
        )

    def test_get_rejects_a_locked_or_missing_secret(self) -> None:
        collection = mock.Mock()
        collection.is_locked.return_value = True
        service = object.__new__(_SecretService)
        service._collection = collection
        with self.assertRaisesRegex(Exception, "locked"):
            service.get("name")

        collection.is_locked.return_value = False
        collection.search_items.return_value = iter([])
        with self.assertRaisesRegex(Exception, "No stored"):
            service.get("name")

    def test_set_rejects_a_locked_collection(self) -> None:
        collection = mock.Mock()
        collection.is_locked.return_value = True
        service = object.__new__(_SecretService)
        service._collection = collection

        with self.assertRaisesRegex(Exception, "locked"):
            service.set("name", "secret")

    def test_init_translates_secret_service_connection_errors(self) -> None:
        secretstorage = mock.Mock()
        secretstorage.get_default_collection.side_effect = OSError("unavailable")
        with (
            mock.patch.dict(sys.modules, {"secretstorage": secretstorage}),
            self.assertRaisesRegex(KeyringError, "Cannot access"),
        ):
            _SecretService()

    def test_get_rejects_locked_items_and_translates_backend_errors(self) -> None:
        item = mock.Mock()
        item.is_locked.return_value = True
        collection = mock.Mock()
        collection.is_locked.return_value = False
        collection.search_items.return_value = [item]
        service = object.__new__(_SecretService)
        service._collection = collection

        with self.assertRaisesRegex(KeyringError, "item is locked"):
            service.get("name")

        collection.search_items.side_effect = OSError("unavailable")
        with self.assertRaisesRegex(KeyringError, "Cannot retrieve"):
            service.get("name")

    def test_set_translates_backend_errors(self) -> None:
        collection = mock.Mock()
        collection.is_locked.return_value = False
        collection.create_item.side_effect = OSError("unavailable")
        service = object.__new__(_SecretService)
        service._collection = collection

        with self.assertRaisesRegex(KeyringError, "Cannot store"):
            service.set("name", "secret")
