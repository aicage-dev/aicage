# Task 42 design gates

> This is as much AI-slop as it gets. Not really readable to humans. *sigh*

## Sidecar runtime identity

Do not leave the credential sidecars running as the image default user merely because the image currently defaults to
root. On Unix, the sidecar must run with the effective target-container UID/GID (normally the invoking host user's
numeric identity), so the sockets it creates in the named volume are usable by the target container without broadening
socket permissions. Resolve this consistently with Aicage's existing target-container identity logic. Windows and
rootless Docker need an explicit, tested mapping because the current target-container identity may legitimately be
root in those environments.

Keep the utility image UID-agnostic and set the runtime user when Aicage creates the sidecar; do not bake a fixed UID
or ownership into the image. Test socket ownership and connection as the target-container user for both protocols.

`aicage-image-util:agent-version` also currently runs with its image-default user. Audit its invocation separately:
it is a short-lived, read-only version-script runner rather than a credential sidecar, so do not change it under this
task without confirming its required file ownership and execution behavior.

## Native keyring behaviour

Before implementing automated encrypted SSH-key loading, validate the intended operating-system keyring API on Linux
and Windows. macOS remains unvalidated locally; see its platform note below.

`aicage` does not currently use a keyring client. The intended design is for Aicage itself to call the platform keyring
service under the invoking user's account; it must not require a separate credential tool.

### General requirements

Store passphrases by public-key fingerprint. Use a stable, namespaced credential name, for example
`aicage/ssh/passphrase/<SSH-SHA256-fingerprint>` or `aicage/gpg/passphrase/<GPG-subkey-fingerprint>`.

A noninteractive run must fail before target-container startup if the secret is unavailable in the platform store,
inaccessible, locked, or would require a prompt. If validation succeeds, an interactive configuration run obtains the
passphrase once and stores it through the native keyring API. A later run retrieves the raw secret only transiently,
then hands it to a one-time sidecar loading command through stdin. It must not occur in command arguments, target
environment, sidecar configuration, labels, logs, or socket volumes. No design can avoid brief plaintext process
memory when a passphrase must be supplied to `ssh-add`.

The platform keyring can store passphrases for both SSH and GnuPG keys, but it does not solve agent-loading semantics.
`ssh-add` needs a controlled askpass-helper/file-descriptor design rather than assuming it accepts a passphrase
directly on stdin. GnuPG can accept a passphrase via a loopback pinentry file descriptor for a focused operation, but
preloading `gpg-agent` has separate keygrip, pinentry, and cache rules; define and test that sidecar command contract
without placing a passphrase in arguments or environment variables.

### Linux validation (2026-11-05)

Validated on Nobara Linux 44 / KDE Plasma: use the freedesktop.org Secret Service API
(`org.freedesktop.secrets`) as the Linux platform-keyring API. On this host it is provided by KDE `ksecretd`, backed
by KWallet. A temporary item was stored, retrieved by a fresh client process, deleted, and confirmed absent using
the user-session service. The default collection was unlocked and exposes the standard `Locked`, `Lock`, and
`Unlock` API.

Implementation must treat a missing session bus/service, D-Bus access denial, a locked collection/item, a missing
secret, or an operation that would require an unlock prompt as a clear noninteractive failure before target-container
startup. The validation client (`secret-tool`) is not an Aicage runtime dependency; select a Python client that uses
the same Secret Service API.

Validate that an Aicage-created item can be created, retrieved from a fresh Aicage process, and deleted. Check locked
store and denied-access behaviour.

### Windows validation (2026-11-05)

Validated on this Windows host: use Windows Credential Manager's native `CredWriteW`, `CredReadW`, and
`CredDeleteW` APIs with `CRED_TYPE_GENERIC` credentials as the Windows platform-keyring API. A temporary generic
credential was written, read back by a fresh PowerShell process through `CredReadW`, deleted, and confirmed absent.
The validation command used the built-in `cmdkey` only to create/delete the temporary item; it is not an Aicage
runtime dependency. Aicage must call the native APIs itself under the invoking user's token. Use
`CRED_PERSIST_LOCAL_MACHINE`; generic credentials hold application-defined secret data and persist across later
logons of the same user on the same machine. They are not an application-isolated store: another process running as
that user can access them, which is the normal Windows Credential Manager security boundary.

Unlike Secret Service, Credential Manager has no separate locked-store or unlock-prompt state for a normal
interactive user token. `CredReadW` is noninteractive, so the same-user noninteractive reload path can retrieve a
stored passphrase without a prompt. Treat `ERROR_NOT_FOUND`, `ERROR_NO_SUCH_LOGON_SESSION` (including a token with
no associated credential set), and other native API failures as clear failures before target-container startup.

The current Aicage environment has no `keyring` package. Python `keyring`'s `WinVaultKeyring` backend can use
Credential Manager but adds a `pywin32`/`pywin32-ctypes` dependency and its automatic backend selection may be
affected by configuration. Prefer a narrow direct `ctypes` wrapper around the three Credential Manager APIs, or
explicitly select and verify that backend; do not silently fall back to a file or other configured backend.

### macOS platform note (unvalidated)

No macOS hardware is available for local validation, and macOS support is currently limited to basic CI coverage that
may itself need repair. Do not block implementation on a pre-implementation macOS keyring test. Implement the native
Keychain path with the same noninteractive guarantees as the other platforms, then use GitHub macOS CI after
implementation to expose compatibility issues. This is a known best-effort risk, not evidence that Keychain behaves
like the Linux Secret Service.

When macOS validation becomes feasible, confirm that an Aicage-created item can be created, retrieved from a fresh
Aicage process, and deleted; check missing-secret and denied-access behaviour. The Python CLI must have an acceptable
approval experience. Do not assume a client is authorized merely because it runs as the logged-in user.
