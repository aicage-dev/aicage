# Task 42 test coverage

This document assigns test responsibilities between `aicage-image-util` and `aicage`. It records the observed
coverage at the beginning of the sidecar implementation so that later work does not mistake image-level tests for
end-to-end Aicage coverage.

Both repositories should test cross-container SSH and GnuPG use. They exercise different contracts:

- `aicage-image-util` proves the credential-agent image with synthetic credentials, Docker containers, and named
  volumes. It must be independent of a real user's keys, host agent, keyring, or project configuration.
- `aicage` proves that its configuration, host inspection, keyring integration, Docker resource manager, and target
  container mount layout select and invoke that image correctly on supported hosts.

## Current `aicage-image-util` coverage

`images/credential-agent/test.sh` is a live Docker test executed by the credential-image workflow on Linux amd64 and
arm64 builders. It currently covers:

- SSH sidecar startup and readiness: a second container runs `ssh ready` through the shared named volume.
- GnuPG sidecar startup and readiness: a second container runs `gpg ready` through the shared named volume.
- Dispatcher errors: empty and unsupported SSH/GnuPG commands fail rather than starting an unintended mode.
- Encrypted SSH key loading: the test generates an encrypted Ed25519 key, mounts it read-only into the sidecar,
  supplies the passphrase on stdin, and uses `ssh-add -l` from another container through the socket volume.
- SSH client signing: a separate client with only the generated public key creates an agent-backed signature through
  the read-only socket volume, and another container verifies it against an allowed-signers file.
- SSH authentication: a separate client with no private-key mount authenticates through the socket volume to an
  ephemeral test-only `sshd` whose `authorized_keys` contains only the generated public key.
- Unencrypted SSH key loading: the test loads a generated unencrypted Ed25519 key and lists it through the socket
  volume from a separate container.
- SSH failure behavior: incorrect and absent passphrases fail without hanging; the absent-passphrase test has a
  five-second timeout.
- SSH sidecar recreation: two identities load into one agent; replacing the sidecar while retaining its socket volume
  produces an empty agent, and an explicit reload restores an identity.
- Encrypted GnuPG key loading: the test creates a protected synthetic GnuPG key, mounts its home read-only into the
  sidecar, supplies the passphrase on stdin, and signs inside the sidecar.
- GnuPG failure behavior: an incorrect passphrase is rejected during `gpg load`, and absent stdin fails without
  hanging; the absent-passphrase test has a five-second timeout.
- GnuPG client signing: a separate container uses its own public-key-only GnuPG home and a socket symlink into the
  shared volume to sign with an unprotected synthetic key; a third container verifies that signature using only the
  public key.
- Protected GnuPG client signing: the sidecar receives the generated key's passphrase on stdin, then a separate
  client signs through the shared socket volume and a public-key-only third container verifies the signature.
- Runtime user ownership: credential-loading tests chown the fresh socket volume and run the sidecar as the invoking
  numeric UID:GID; SSH readiness succeeds as that numeric user both before and after sidecar recreation.
- Socket-volume isolation: tests assert that the shared socket volume has no regular files after use. Client GnuPG
  state is deliberately kept in its separate home rather than being written to that volume.

This is live image coverage, not a mock suite. It does not use a real host credential directory or keyring.

## Required `aicage-image-util` coverage

Add the following focused image-contract tests:

- Assert that the client containers and socket volume contain no private keyring, secret-key directory, or passphrase
  material. Allow only expected socket and directory artifacts in the volume.

The image repository does not need to test host SSH configuration discovery, a real operating-system keyring, Windows
named pipes, or Aicage configuration scopes. Those are Aicage responsibilities.

## Required `aicage` coverage

### Unit tests

- Resource inspection, ownership rejection, creation, stopped/unhealthy/obsolete replacement, retained volumes,
  readiness failures, lock contention, and one shared image resolution for both protocols.
- Protocol selection: usable Unix host socket selects direct forwarding; unusable socket selects a sidecar; Windows
  always selects a sidecar and never requests a Windows named-pipe mount.
- `DockerRunArgs` volume mounts and protocol environment for each selection, with no target private-key mounts.
- SSH/GnuPG host support files retained read-only in the target container.
- Keyring lookup/store, passphrase fingerprint mapping, reload, and clear noninteractive missing-secret errors.

### Integration and platform tests

- Linux direct SSH and GnuPG forwarding remains functional when the host socket is bind-mountable.
- Linux fallback sidecars provide SSH authentication and GnuPG signing from an actual Aicage target container.
- Windows Docker Desktop/WSL target containers use only socket volumes; they do not mount
  `\\.\pipe\openssh-ssh-agent` or alter/start the Windows OpenSSH service.
- A target container signs through the volume-backed GnuPG socket on Linux and Windows without private-key mounts.
- Stop or remove either singleton sidecar, retain its volume, then confirm the next relevant Aicage run recreates and
  reloads it.
- Terminal configuration, global configuration, and tree configuration all perform required SSH setup when sharing is
  enabled.
- First encrypted-key setup, post-reboot sidecar reload, and noninteractive missing-keyring-secret failure behave as
  specified.
- Run the platform-specific cases on the Aicage CI matrix, where native host and target-image behavior is available.

## Scope boundary

An image test may reproduce the generic target-container shape using only synthetic credentials and a named volume.
That overlap is intentional. It detects regressions in the helper image before Aicage orchestration is involved.

An Aicage integration test must not assume the helper-image tests make its host-specific behavior safe. It remains
responsible for mount selection, user identity mapping, credential discovery, keyring interaction, resource
orchestration, and platform restrictions.
