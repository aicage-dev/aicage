# Task 42 implementation plan

## Scope

Implement persistent SSH and GnuPG credential sidecars in `aicage` and a dedicated
`aicage-image-util:credential-agent` image. Do not change `aicage-image-base`.

The sidecars are global Docker singleton resources, not project resources:

- SSH: container `aicage-ssh-agent`, volume `aicage-ssh-agent-socket`
- GnuPG: container `aicage-gpg-agent`, volume `aicage-gpg-agent-socket`

Both have `org.aicage.resource=credential-agent`, a protocol label, and a helper image/protocol version label.
Socket volumes persist across ordinary Aicage exits and are never mounted with host credential directories.

The private-key restriction applies to target/agent containers, not to the narrowly scoped credential sidecars. When
direct host-agent forwarding is unavailable, a credential sidecar may receive only the host private-key material it
needs, read-only; it must expose only its agent socket to target containers.

See [design gates](DESIGN_GATES.md) before implementing the corresponding work.
See [test coverage](TEST_COVERAGE.md) for the current evidence and required test ownership by repository.

## Commit 1: `aicage-image-util` credential image

**Status: complete.** Completed in `aicage-image-util` commit `d113eb1` and the current working tree:

- separate Alpine `credential-agent` image, dispatcher, SSH/GnuPG sidecar startup and readiness;
- socket-volume cross-container readiness tests;
- independent variant/architecture build and multi-architecture publish workflow, attestations, signing, cleanup, and
  purpose-qualified version and stable tags;
- symmetric `images/agent-version` and `images/credential-agent` layout;
- explicit SSH and GnuPG key-loading command contracts, with passphrases received only through standard input;
- encrypted SSH and GnuPG credential-loading tests, including non-root sidecar ownership and signing through the GnuPG
  sidecar;
- socket-volume isolation tests confirming it contains no regular credential files; and
- development documentation for purpose-qualified version tags.

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

**Status: complete.** The private credential-agent runtime package now owns shared credential-image setup, labelled
singleton resource inspection and replacement, volume retention, socket readiness, volume ownership preparation, and
the global creation lock. Protocol selection and host credential mounts remain deferred to Commit 3.

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

Keep GnuPG's agent and pinentry lifecycle inside its sidecar. Define its interactive and noninteractive behaviour as
part of the image command contract before implementation.

For passphrase-protected GnuPG secret keys that must be usable noninteractively, use the same platform-keyring pattern:
store the passphrase by the relevant secret-key or subkey fingerprint, retrieve it only transiently, and provide it to a
one-time sidecar operation through stdin. The target container must never receive the passphrase or private-key files.
This does not replace the sidecar's interactive pinentry, smartcard, cache, or key-selection behaviour; that command
contract still needs to define those cases.

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
