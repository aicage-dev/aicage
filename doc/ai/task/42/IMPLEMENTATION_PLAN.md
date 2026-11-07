# Task 42 implementation plan

## Scope

Implement persistent SSH and GnuPG credential sidecars in `aicage` and a dedicated
`aicage-image-util:credential-agent` image. Do not change `aicage-image-base`.

The sidecars are global Docker singleton resources, not project resources:

- SSH: container `aicage-credential-agent-ssh`, volume `aicage-credential-agent-ssh-socket`
- GnuPG: container `aicage-credential-agent-gpg`, volume `aicage-credential-agent-gpg-socket`

Both have `org.aicage.resource=credential-agent`, a protocol label, and a helper image/protocol version label.
Socket volumes persist across ordinary Aicage exits and are never mounted with host credential directories.

The private-key restriction applies to target coding-agent containers, not to the narrowly scoped credential sidecars.
When direct host-socket forwarding is unavailable, a credential sidecar may receive only the host private-key material
it needs, read-only; it exposes only its credential socket to target containers.

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
credential-agent ssh
credential-agent gpg
```

The SSH mode starts `ssh-agent` on the volume-backed socket and exposes a readiness command plus explicit key loading.
The GnuPG mode starts `gpg-agent` with credential material only in the sidecar and relays its normal socket into the
named volume, plus a readiness command. Both modes must be noninteractive when invoked noninteractively.

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

Unit-test ownership inspection, missing/stopped/obsolete replacement, volume retention, readiness failure, and
concurrent creation. Ensuring SSH and GnuPG in the same run must resolve/update the credential image only once.

## Commit 3: `aicage` forwarding selection and sidecar lifecycle

**Status: complete.** The public credential-agent forwarding coordinator now selects a prepared Linux host SSH agent
and a reachable Unix GnuPG agent socket for direct forwarding, and otherwise uses the persistent sidecar (always on
Windows). It adds protocol-specific named
volume mounts and environments to `DockerRunArgs`, preserves SSH/GnuPG public support mounts, mounts credential homes
read-only only in sidecars, uses the target-container runtime UID/GID for sidecars, and removes the Windows OpenSSH
service-management path and direct GnuPG resolver. Global and tree configuration saves ensure required SSH sidecars.
Unit tests cover direct and fallback selection, Windows named-pipe avoidance, SSH/GnuPG target mount arguments,
credential-sidecar mounts, resource replacement and lock errors, and target identity mapping.

Replace the current separate SSH and GnuPG forwarding paths with one protocol-aware coordinator:

- Linux: prefer the prepared host SSH agent; select the SSH sidecar when unavailable. Retain direct GnuPG forwarding
  when its host agent socket is reachable and bind-mountable; select the GnuPG sidecar otherwise.
- Windows: always select the sidecar; never start or modify the Windows OpenSSH service and never mount a Windows named
  pipe.
- Ensure the required image once, then volume and singleton sidecar for each selected protocol, and verify its socket
  before target startup.
- Add only protocol socket-volume mounts and agent environment settings to `DockerRunArgs`.
- Preserve existing read-only SSH configuration, known-host, and public-key mounts, and read-only GnuPG public-keyring,
  trust, and configuration mounts. Remove direct private-key and host credential-socket mounts from target containers.

Move SSH setup out of the target-run-only path so global and tree configuration saves also perform required terminal SSH
setup when SSH sharing is enabled.

## Commit 4: protected-key behavior

**Status: complete.** The native-platform-keyring proposal was superseded. Protected-key passphrases stay outside
Aicage and are entered directly into `ssh-add` or GnuPG pinentry during interactive setup. A noninteractive run never
prompts; it warns and continues without a protected identity that is not already usable. Unprotected SSH keys reload
after a host service or sidecar restart.

## Commit 5: `aicage` integration and platform coverage

**Status: complete.** The live Docker matrix covers direct-host SSH forwarding, SSH sidecar fallback, and GnuPG
signing. Linux covers both direct GnuPG forwarding and a forced sidecar fallback; Windows covers its required
sidecar-only GnuPG path. The
Host-key discovery and mount defaults are independent of Git configuration. The SSH test verifies credential-backed
signing, verification, isolated SSH authentication,
target private-key-path absence,
and restart/reload. The GnuPG tests verify signing, target `GNUPGHOME` private-key-file isolation, and sidecar
restart/reload. Protected-key integration tests use real encrypted fixtures, sidecars, and client socket volumes. They
cover interactive setup, public-only client use, restart behavior, and the noninteractive warning-and-continue
behavior.

The temporary credential-focused CI matrix filter has been removed; normal non-proxy integration discovery is restored.

## Documentation

Keep technical process notes in development documentation, not the main README.
