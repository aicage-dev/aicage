# Task 42: Cross-platform SSH and GnuPG forwarding with persistent utility sidecars

See [test coverage](TEST_COVERAGE.md) for the current evidence and the division of test responsibilities between
`aicage-image-util` and `aicage`.

## Current implementation status

Commits 1 through 4 are complete. `aicage-image-util` provides the published `credential-agent` helper image, and
`aicage` selects direct Unix forwarding where possible, otherwise manages the persistent SSH/GnuPG sidecars. SSH
sidecar setup and encrypted-key reload use the platform keyring on Linux, Windows, and macOS.

The remaining work is Commit 5: live Aicage integration and platform-matrix coverage. In particular, the existing
unit tests do not replace a real Linux fallback, Windows Docker Desktop/WSL, sidecar restart, or GnuPG signing test.

## Problem

The SSH and GnuPG refactors replaced mounting host credential homes directly into agent containers with agent-socket
forwarding. Direct forwarding remains the preferred Unix path because the agents expose Unix-domain sockets that Docker
can bind mount.

It does not work for a native Windows host running Linux containers through Docker Desktop:

- Windows OpenSSH exposes `\\.\pipe\openssh-ssh-agent`, a Windows named pipe.
- Docker Desktop cannot bind mount that pipe into a Linux container as a Unix-domain socket. Git Bash translates the
  source to `/pipe/openssh-ssh-agent`, which Docker rejects; a Windows AF_UNIX socket bind mount also reaches the
  container unreliably (`Connection refused` in Windows CI).
- Native Windows GnuPG has the same host-IPC-to-Linux-container boundary. Its agent cannot be forwarded directly as a
  Linux Unix-domain socket either.
- Aicage must not alter Windows services, change private-key ACLs, require users to preload identities in a host
  agent, or introduce a new host-side credential-tool dependency.

## Desired design

Use sidecars only when direct host-agent forwarding is unavailable. Windows always uses two persistent,
aicage-managed sidecars and two persistent Docker volumes. Unix hosts retain direct forwarding when Aicage can use and
mount a host agent socket; they use the relevant sidecar only when that path cannot be established. Both sidecars use
one dedicated `aicage-image-util:credential-agent` image, invoked explicitly in an SSH or GnuPG mode. This uses the
existing image release, signature, and update lifecycle without adding a helper image per protocol.

```text
host ~/.ssh  (mounted only into utility sidecar)
       |
       v
aicage-image-util:credential-agent ssh sidecar
       |
       | SSH Unix socket in a persistent named volume
       v
one or more aicage agent containers

host GNUPGHOME  (mounted only into utility sidecar)
       |
       v
aicage-image-util:credential-agent gpg sidecar
       |
       | GnuPG Unix socket in a persistent named volume
       v
one or more aicage agent containers
```

Target containers mount only the socket volumes for the enabled protocols. SSH containers receive `SSH_AUTH_SOCK` and
retain Aicage's existing read-only mounts for SSH configuration, known-hosts files, and public-key files. GnuPG
containers receive the GnuPG agent socket and retain its existing read-only public keyring, trust, and configuration
files. They never receive private-key files.

### Persistent singleton resources

Use separate stable names and aicage ownership labels, for example:

- SSH container: `aicage-ssh-agent`; volume: `aicage-ssh-agent-socket`
- GnuPG container: `aicage-gpg-agent`; volume: `aicage-gpg-agent-socket`
- labels: `org.aicage.resource=credential-agent`, a protocol label, and a helper-image/protocol version label

They intentionally survive ordinary aicage exits. When a run requires either sidecar, aicage should:

1. Resolve and update the shared credential-helper image once using the existing image digest/signature/pull lifecycle.
2. For each enabled protocol, ensure its named volume and singleton sidecar exist.
3. Replace an absent, stopped, unhealthy, or obsolete sidecar while retaining its volume.
4. Verify each required socket before starting the target agent container.
5. Mount each required volume in the target container and set its protocol environment.

Docker restarts leave harmless stale socket entries in the volumes; aicage recreates the required sidecars and sockets
on the next run. A short host-side lock is needed only to prevent concurrent aicage invocations racing while creating
or replacing either singleton.

The global scope is intentional: each sidecar serves all projects that enable its protocol, so separate projects do
not have separate key scope.

## Credential-helper image

Do not depend on the Windows OpenSSH service, Windows private-key ACLs, or native Windows GnuPG agent IPC. Sidecars
run Linux OpenSSH and GnuPG tools in the Docker environment and can use the same host credential directories that
previous aicage versions mounted directly.

`aicage-image-util:agent-version` is currently a Node-based general-purpose image (about 98 MB content size / 375 MB
Docker disk usage locally). Build a separate, small `aicage-image-util:credential-agent` tag with only an Alpine base,
OpenSSH client tools, GnuPG, and its sidecar scripts. Keep `agent-version` unchanged so credential forwarding does not
pull Node and Python. The credential image has one small dispatcher invoked as `aicage-credential-agent ssh` or
`aicage-credential-agent gpg`; each mode runs its own focused script and readiness check.

One credential-image digest check covers both sidecars, so enabling both protocols does not add a second helper-image
update request. Do not add this helper to `aicage-image-base` unless a later design need proves it necessary. Target
images need only their existing SSH and GnuPG clients plus the relevant volume-backed agent sockets; the utility image
owns sidecar behavior when the sidecar path is selected.

## Passphrase handling

When SSH sharing is enabled in the terminal configuration UI, its existing confirmation dialog also authorizes SSH
setup. Aicage creates/updates the sidecar there. For an encrypted key, it first looks up a passphrase in the
operating-system keyring by public-key fingerprint and asks only when no entry exists. There is no separate setup
command.

After a reboot, the sidecar agent is empty. Aicage loads each key again before starting a target container: directly
for an unencrypted key, or by retrieving its passphrase from the operating-system keyring. On Linux use the
freedesktop.org Secret Service API; use the platform's normal credential store on Windows and macOS.

A noninteractive invocation must never prompt. If it finds an encrypted key whose passphrase is not in the keyring,
it stops before starting the target container and tells the user to open the normal terminal configuration UI to add
that key.

Global and tree shared-configuration edits must perform the same terminal SSH setup when SSH sharing is enabled, even
though they do not start a target agent container.

The GnuPG sidecar owns its GnuPG agent lifecycle and pinentry behavior. Its noninteractive behavior must likewise never
prompt. For passphrase-protected GnuPG secret keys that must be used noninteractively, Aicage stores the passphrase in
the platform keyring by the relevant secret-key or subkey fingerprint and passes it only transiently, via stdin, to a
one-time sidecar operation. This complements rather than replaces the sidecar's interactive pinentry, smartcard, cache,
and key-selection behavior. The socket volumes never contain private keys or passphrases.

## Implementation areas

### `aicage-image-util`

- Build and release `aicage-image-util:credential-agent`, separate from `agent-version`.
- Include OpenSSH and GnuPG tools plus a dispatcher with `ssh` and `gpg` modes.
- Define and test a focused startup and readiness command for each agent socket.
- Publish it through the existing `aicage-image-util` release and image workflow.
- Do not mount host credential material into either socket volume.

### `aicage`

- Prefer direct host-agent forwarding on Unix. Select the SSH or GnuPG sidecar when direct forwarding is unavailable,
  and always select sidecars on Windows.
- Add a Docker resource manager for the labelled SSH and GnuPG singleton volumes and sidecars.
- Reuse the established helper-image digest, signature verification, pull, and old-digest cleanup code once for the
  shared credential image.
- Add a short creation/replacement lock.
- Add each enabled protocol's volume mount and agent environment to `DockerRunArgs`.
- Retain the existing read-only target-container mounts for SSH configuration, known-hosts files, and public-key
  files, plus the existing GnuPG public keyring, trust, and configuration mounts; remove only direct private-key and
  host-agent-socket mounts.
- Remove direct host agent-socket bind mounts on Windows.

### Tests

- Unit tests for resource inspection, creation, replacement, lock behavior, and protocol-specific socket mount
  arguments.
- Utility-image tests for SSH and GnuPG mode startup, readiness, and credential-loading behavior.
- Linux integration tests: retain direct SSH/GnuPG agent forwarding when usable; fall back to a sidecar when direct
  forwarding cannot be established.
- Windows integration test: Docker Desktop/WSL target container sees the same identities through the volume-backed
  socket; it must not mount a Windows named pipe or require the Windows OpenSSH service.
- GnuPG integration tests: target container signs through the volume-backed GnuPG agent on Linux and Windows without
  private-key mounts.
- Restart integration tests: remove/stop either sidecar and verify the next relevant run recreates it while retaining
  its named volume.
- Test SSH initial passphrase setup, post-reboot keyring reload, and the noninteractive missing-passphrase error.

## Non-goals and constraints

- Never change Windows service state/startup policy.
- Never change Windows key permissions/ACLs.
- Never require an additional host-side credential tool.
- Never mount private keys in target agent containers.
- Do not create per-run sidecars or per-run volumes.
- Do not delete either singleton socket volume during ordinary aicage shutdown.
- Discuss with the user before modifying `aicage-image-base`, especially `scripts/entrypoint.sh`.
