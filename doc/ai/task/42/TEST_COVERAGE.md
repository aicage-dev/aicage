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

`images/credential-agent/test.bats` is a live Docker suite executed by the credential-image workflow on Linux amd64
and arm64 builders. It currently covers:

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
  sidecar, and supplies the passphrase on stdin. An incorrect passphrase is accepted by `gpg load` but the subsequent
  signing operation fails; loading the correct passphrase then permits signing inside the sidecar.
- GnuPG missing-passphrase behavior: a protected `gpg load` with closed stdin fails within five seconds, without an
  interactive pinentry or data written to the socket volume.
- GnuPG client signing: a separate container uses its own public-key-only GnuPG home and a socket symlink into the
  shared volume to sign with an unprotected synthetic key; a third container verifies that signature using only the
  public key.
- Protected GnuPG client signing: `gpg load` seeds both the normal sidecar-local cache and the GnuPG restricted cache
  used by extra-socket clients. A separate public-key-only client then signs through the restricted socket volume and
  a third container verifies the signature. The expected restricted-socket `Forbidden` key-listing diagnostic does
  not prevent signing and is not a test failure.
- Runtime user ownership: credential-loading tests chown the fresh socket volume and run the sidecar as the invoking
  numeric UID:GID; SSH readiness succeeds as that numeric user both before and after sidecar recreation.
- Socket-volume isolation: tests assert that every shared-volume entry is a Unix socket; it cannot contain files,
  directories, symlinks, or other artifacts. Client GnuPG state is deliberately kept in its separate home rather than
  being written to that volume.
- GnuPG client isolation: after signing, both the simulated target and independent verifier homes have no files in
  `private-keys-v1.d`, no legacy `secring.gpg`, and no secret keys reported by `gpg --list-secret-keys`. The protected
  key case also scans all client-home regular files for the supplied passphrase. GnuPG may create an otherwise empty
  `private-keys-v1.d` directory even for a public-only home.

This is live image coverage, not a mock suite. It does not use a real host credential directory or keyring.

## Current `aicage` unit coverage

The `aicage` unit suite covers credential-image selection, singleton sidecar/volume lifecycle, direct-versus-sidecar
forwarding, target mount arguments, SSH key discovery and reload, and the platform keyring implementations. Relevant
test modules include:

- `tests/aicage/runtime/credential_agent/test__resource_lifecycle.py` for labelled singleton resources, replacement,
  locks, retained volumes, and readiness;
- `test__ssh_forwarding.py` and `test__gpg_forwarding.py` for forwarding selection and target arguments;
- `keyring/test__secret_service.py`, `keyring/test__windows.py`, and `keyring/test__macos.py` for native-store success
  and failure behavior; and
- configuration tests for interactive setup and noninteractive reload behavior.

On 2026-11-07, `pytest --cov=src --cov-report=term-missing` completed with 1002 passed, 42 skipped, and 94% total
line coverage. The four implemented platform/SSH modules named in the Commit 4 status have 100% targeted line
coverage. This is unit evidence only; the required integration cases remain pending.

## Required `aicage-image-util` coverage

None currently identified. A completed container test cannot inspect transient process memory.

The image repository does not need to test host SSH configuration discovery, a real operating-system keyring, Windows
named pipes, or Aicage configuration scopes. Those are Aicage responsibilities.

## Required `aicage` coverage

The unit-test items in this section are complete for the implemented SSH/keyring and sidecar lifecycle behavior. Basic
integration coverage is now present, but protected-key, replacement/reload, and full-matrix cases remain Commit 5
work.

### Unit tests

- Resource inspection, ownership rejection, creation, stopped/unhealthy/obsolete replacement, retained volumes,
  readiness failures, lock contention, and one shared image resolution for both protocols.
- Protocol selection: SSH always selects a sidecar; GnuPG uses direct Unix forwarding when usable and a sidecar
  otherwise; Windows always selects sidecars and never requests a Windows named-pipe mount.
- `DockerRunArgs` volume mounts and protocol environment for each selection, with no target private-key mounts.
- SSH/GnuPG host support files retained read-only in the target container.
- Keyring lookup/store, passphrase fingerprint mapping, reload, and clear noninteractive missing-secret errors.

### Integration and platform tests

Completed basic live coverage:

- Linux direct GnuPG forwarding remains functional when the host socket is bind-mountable; forced fallback-sidecar
  GnuPG signing is also covered.
- Windows Docker Desktop/WSL covers the required sidecar-only GnuPG path and SSH sidecar identity availability.
- A target container signs through the volume-backed GnuPG socket on Linux and Windows without private-key files in
  its temporary GnuPG home.
- SSH sidecar identities and public support files are available in the target, while configured private-key paths are
  absent; the target signs and verifies a message through the sidecar socket, then authenticates to an isolated SSHD
  through that socket.
- Stopping the SSH sidecar preserves its volume; the next Aicage run restarts it, reloads keys, and signs again.
- Stopping the GnuPG sidecar preserves its volume; the next Aicage run restarts it and signs a second commit without
  private-key files in the target GnuPG home.

Still required:

- Protected SSH initial setup, post-reboot reload, and noninteractive missing-keyring-secret behavior.
- Protected GnuPG sidecar signing with a keyring-retrieved passphrase.
- Place the SSH fixture outside target-mounted checkout paths, matching the GnuPG fixture's isolation.
- Remove the temporary Task 42 CI-matrix filter and run the restored non-proxy integration suite on the relevant
  platform matrix.
- Run the platform-specific cases on the Aicage CI matrix, where native host and target-image behavior is available.

## Scope boundary

An image test may reproduce the generic target-container shape using only synthetic credentials and a named volume.
That overlap is intentional. It detects regressions in the helper image before Aicage orchestration is involved.

An Aicage integration test must not assume the helper-image tests make its host-specific behavior safe. It remains
responsible for mount selection, user identity mapping, credential discovery, keyring interaction, resource
orchestration, and platform restrictions.
