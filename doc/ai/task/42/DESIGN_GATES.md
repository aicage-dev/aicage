# Task 42 design decisions

This document records the decisions that remain relevant to the completed implementation. The working code is the
source of truth.

## Sidecar runtime identity

Credential sidecars run as the target-container UID/GID. The utility image remains UID-agnostic; Aicage supplies the
runtime identity when it creates a sidecar. This lets the target container use the sockets in the named volume without
broad socket permissions. Root-compatible Windows and rootless-Docker mappings are covered by the runtime identity
logic and tests.

`aicage-image-util:agent-version` is a separate short-lived utility invocation. Task 42 does not change its image
default user.

## Protected keys and passphrases

The discarded platform-keyring design must not be reintroduced implicitly. Aicage does not read, store, or reload
private-key passphrases.

- An interactive run may let `ssh-add` or GnuPG pinentry ask for a protected key's passphrase directly in the selected
  host credential service or sidecar.
- A noninteractive run never prompts. If a protected key is not already usable, Aicage logs a warning and starts the
  coding-agent container without that identity.
- An unprotected SSH key is reloaded when a selected host service or sidecar is empty.
- Socket volumes contain sockets only; they contain neither credential files nor passphrases.

This behavior is intentionally different from the earlier proposed native Keychain, Credential Manager, and Secret
Service integration. Those investigations were planning material only and are not part of the implementation.
