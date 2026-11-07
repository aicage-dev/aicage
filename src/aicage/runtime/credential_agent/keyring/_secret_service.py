"""Linux freedesktop.org Secret Service backend."""

from ._base import _Keyring
from .errors import KeyringError, SecretNotFoundError


class _SecretService(_Keyring):
    """Secret Service, accessed through the invoking user's session bus."""

    _ATTRIBUTES = "aicage.credential"

    def __init__(self) -> None:
        try:
            import secretstorage  # type: ignore[import-not-found]  # noqa: PLC0415
        except ImportError as exc:  # pragma: no cover - packaging/platform failure.
            raise KeyringError("Secret Service support is unavailable.") from exc
        try:
            self._collection = secretstorage.get_default_collection(
                secretstorage.dbus_init()
            )
        except (
            Exception
        ) as exc:  # Secret Service library has backend-specific exceptions.
            raise KeyringError("Cannot access the user Secret Service.") from exc

    def get(self, name: str) -> str:
        try:
            if self._collection.is_locked():
                raise KeyringError("The default Secret Service collection is locked.")
            items = list(self._collection.search_items({self._ATTRIBUTES: name}))
            if not items:
                raise SecretNotFoundError("No stored passphrase is available.")
            item = items[0]
            if item.is_locked():
                raise KeyringError("The Secret Service item is locked.")
            return item.get_secret().decode("utf-8")
        except KeyringError:
            raise
        except (
            Exception
        ) as exc:  # Secret Service library has backend-specific exceptions.
            raise KeyringError(
                "Cannot retrieve the passphrase from Secret Service."
            ) from exc

    def set(self, name: str, secret: str) -> None:
        try:
            if self._collection.is_locked():
                raise KeyringError("The default Secret Service collection is locked.")
            self._collection.create_item(
                f"Aicage credential {name}",
                {self._ATTRIBUTES: name},
                secret.encode("utf-8"),
                replace=True,
            )
        except KeyringError:
            raise
        except (
            Exception
        ) as exc:  # Secret Service library has backend-specific exceptions.
            raise KeyringError(
                "Cannot store the passphrase in Secret Service."
            ) from exc
