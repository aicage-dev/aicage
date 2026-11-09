"""Shared types for platform credential stores."""

from typing import Protocol


class _Keyring(Protocol):
    def get(self, name: str) -> str: ...

    def set(self, name: str, secret: str) -> None: ...
