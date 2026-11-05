# Task 42 implementation plan

## Scope

Implement persistent SSH and GnuPG credential sidecars in `aicage` and a dedicated
`aicage-image-util:credential-agent` image. Do not change `aicage-image-base`.

The sidecars are global Docker singleton resources, not project resources:

- SSH: container `aicage-ssh-agent`, volume `aicage-ssh-agent-socket`
- GnuPG: container `aicage-gpg-agent`, volume `aicage-gpg-agent-socket`

Both have `org.aicage.resource=credential-agent`, a protocol label, and a helper image/protocol version label.
Socket volumes persist across ordinary Aicage exits and are never mounted with host credential directories.

## Design gate: native keyring behaviour

Before implementing automated encrypted SSH-key loading, validate the intended operating-system keyring API on Linux,
Windows, and macOS.

`aicage` does not currently use a keyring client. The intended design is for Aicage itself to call the platform keyring
service under the invoking user's account; it must not require a separate credential tool.

Validate that an Aicage-created item can be created, retrieved from a fresh Aicage process, and deleted. Check locked
store and denied-access behaviour. macOS specifically needs an acceptable approval experience for the Python CLI
process. Do not assume a client is authorized merely because it runs as the logged-in user.

Store passphrases by public-key fingerprint. A noninteractive run must fail before target-container startup if the
secret is missing, locked, inaccessible, or would cause a prompt.

If validation succeeds, an interactive configuration run obtains the passphrase once and stores it through the native
keyring API. A later run retrieves the raw secret only transiently, then hands it to a one-time sidecar loading command
through stdin. It must not occur in command arguments, target environment, sidecar configuration, labels, logs, or
socket volumes. No design can avoid brief plaintext process memory when a passphrase must be supplied to `ssh-add`.

## Commit 1: `aicage-image-util` credential image

Keep the Node-based `agent-version` image and tag unchanged. Add a distinct Alpine-based
`ghcr.io/aicage/aicage-image-util:credential-agent` image with only OpenSSH client tools, GnuPG, and sidecar scripts.

Provide one dispatcher:

```text
aicage-credential-agent ssh
aicage-credential-agent gpg
```

The SSH mode starts `ssh-agent` on the volume-backed socket and exposes a readiness command plus explicit key loading.
The GnuPG mode starts `gpg-agent` with credential material only in the sidecar and exposes its restricted/extra socket
through the named volume, plus a readiness command. Both modes must be noninteractive when invoked noninteractively.

Update the image workflow to build, test, attest, sign, publish, and retain both multi-architecture tags independently.
Add container-level tests covering startup, readiness, socket use from another container through a named volume, and the
absence of credential data in the socket volume.

## Commit 2: `aicage` credential-image and Docker resource foundation

Add a private credential-agent runtime package responsible for:

- the credential image reference, following existing fork/repository configuration conventions;
- shared digest, signature verification, pull, and old-digest cleanup, generalized from the existing version-check image
  lifecycle;
- labelled volume/container inspection, creation, start, removal, and socket readiness;
- protocol constants, names, labels, socket paths, and helper-image version labels;
- a short `portalocker`-based global lock around singleton creation or replacement.

Unit-test ownership inspection, missing/stopped/unhealthy/obsolete replacement, volume retention, readiness failure, and
concurrent creation. Ensuring SSH and GnuPG in the same run must resolve/update the credential image only once.

## Commit 3: `aicage` forwarding selection and sidecar lifecycle

Replace the current separate SSH and GnuPG forwarding paths with one protocol-aware coordinator:

- Unix: retain direct forwarding when a host agent socket is reachable and bind-mountable; select a sidecar otherwise.
- Windows: always select the sidecar; never start or modify the Windows OpenSSH service and never mount a Windows named
  pipe.
- Ensure the required image once, then volume and singleton sidecar for each selected protocol, and verify its socket
  before target startup.
- Add only protocol socket-volume mounts and agent environment settings to `DockerRunArgs`.
- Preserve existing read-only SSH configuration, known-host, and public-key mounts, and read-only GnuPG public-keyring,
  trust, and configuration mounts. Remove direct private-key and host-agent-socket mounts from target containers.

Move SSH setup out of the target-run-only path so global and tree configuration saves also perform required terminal SSH
setup when SSH sharing is enabled.

## Commit 4: `aicage` SSH passphrase and reload lifecycle

After the design gate succeeds, add a narrow private platform-keyring abstraction and SSH setup flow:

- unencrypted keys load into the sidecar directly;
- encrypted keys use a stored passphrase by public-key fingerprint;
- a normal terminal configuration run may prompt and store a missing passphrase;
- recreated or rebooted sidecars reload every required key before target startup;
- noninteractive use never prompts and produces a clear missing-keyring-secret error.

Keep GnuPG's agent and pinentry lifecycle inside its sidecar. Define its interactive and noninteractive behaviour as part of
the image command contract before implementation.

## Commit 5: `aicage` integration and platform coverage

Extend the existing SSH and GnuPG integration suites and Windows workflow to cover:

- Unix direct forwarding when usable;
- Unix fallback to each sidecar when direct forwarding cannot be established;
- Windows Docker Desktop/WSL socket-volume forwarding without a Windows named-pipe mount or Windows OpenSSH service;
- GnuPG signing through the volume-backed socket without target private-key mounts;
- stopping/removing either sidecar and recreating it on the next relevant run while keeping its volume;
- first encrypted SSH-key setup, post-reboot reload, and the noninteractive missing-passphrase error.

## Documentation

Only add user-facing documentation if the final terminal configuration flow or recovery errors require it. Keep technical
process notes in development documentation, not the main README.
