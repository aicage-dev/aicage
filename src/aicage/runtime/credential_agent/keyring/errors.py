"""Errors raised by native credential stores."""


class KeyringError(RuntimeError):
    """The platform credential store could not safely serve a secret."""


class SecretNotFoundError(KeyringError):
    """The requested secret does not exist in the platform credential store."""
