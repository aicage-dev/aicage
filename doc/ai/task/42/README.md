# Task 42: Cross-platform SSH and GnuPG forwarding with persistent utility sidecars

See [test coverage](TEST_COVERAGE.md) for the current evidence and the division of test responsibilities between
`aicage-image-util` and `aicage`.

## Current implementation status

Task 42 is complete. `aicage-image-util` provides the published `credential-agent` helper image. Aicage selects a
usable direct Unix socket where possible and otherwise uses a persistent SSH or GnuPG sidecar; Windows always uses
sidecars. The live Linux and Windows matrix covers direct forwarding, fallback sidecars, signing/authentication,
restart/reload, and target private-key isolation.

SSH and GnuPG are independent credential options. Host credentials make the corresponding `Bind Mounts` row available
in the setup UI; the saved SSH/GnuPG setting decides whether Aicage forwards its socket. Git configuration, remotes,
and signing settings do not participate in that decision.

Protected-key passphrases are entered directly into `ssh-add` or GnuPG pinentry during an interactive run. Aicage does
not read, store, or reload them. A noninteractive run never prompts: it warns and starts without an unavailable
protected identity. Unprotected SSH keys are reloaded into an empty selected host service or sidecar.

## Problem

The SSH and GnuPG refactors replaced mounting host credential homes directly into coding-agent containers with
credential-socket forwarding. Linux SSH and Unix GnuPG prefer a usable host socket because it can be bind mounted
without exposing private keys. SSH falls back to Aicage's sidecar when direct forwarding is unavailable; Windows
always uses the sidecar.

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

Linux SSH forwards the current host `SSH_AUTH_SOCK` after reconciling Aicage-discovered identities into the host SSH
service; the identities remain there. It uses a persistent, aicage-managed sidecar when that path cannot be prepared.
GnuPG uses a sidecar when direct host-socket forwarding is unavailable; Windows always uses both sidecars.
Both sidecars use one dedicated
`aicage-image-util:credential-agent` image, invoked explicitly in an SSH or GnuPG mode. This uses the existing image
release, signature, and update lifecycle without adding a helper image per protocol.

```text
Linux host SSH_AUTH_SOCK
       |
       | bind mount when reachable and prepared
       v
one or more coding-agent containers

host ~/.ssh  (mounted only into utility sidecar fallback)
       |
       v
aicage-image-util:credential-agent ssh sidecar
       |
       | SSH Unix socket in a persistent named volume
       v
one or more coding-agent containers

host GNUPGHOME  (mounted only into utility sidecar)
       |
       v
aicage-image-util:credential-agent gpg sidecar
       |
       | normal GnuPG-agent Unix socket relayed into a persistent named volume
       v
one or more coding-agent containers
```

Target containers receive either a direct host-socket bind mount or a socket volume for each enabled protocol. SSH
containers receive `SSH_AUTH_SOCK` and retain Aicage's existing read-only mounts for SSH configuration, known-hosts
files, and public-key files. GnuPG
containers receive the GnuPG credential socket and retain its existing read-only public keyring, trust, and
configuration files. They never receive private-key files.

### Persistent singleton resources

Use separate stable names and aicage ownership labels, for example:

- SSH container: `aicage-credential-agent-<owner>-ssh`; volume:
  `aicage-credential-agent-<owner>-ssh-socket`
- GnuPG container: `aicage-credential-agent-<owner>-gpg`; volume:
  `aicage-credential-agent-<owner>-gpg-socket`
- labels: `org.aicage.resource=credential-agent`, owner, protocol, and helper-image identity

They intentionally survive ordinary aicage exits. When a run requires either sidecar, aicage should:

1. Resolve and update the shared credential-helper image once using the existing image digest/signature/pull lifecycle.
2. For each enabled protocol, ensure its named volume and singleton sidecar exist.
3. Create a missing sidecar, restart a stopped sidecar, or replace an obsolete sidecar while retaining its volume.
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
pull Node and Python. The credential image has one small dispatcher invoked as `credential-agent ssh` or
`credential-agent gpg`; each mode runs its own focused script and readiness check.

One credential-image digest check covers both sidecars, so enabling both protocols does not add a second helper-image
update request. Do not add this helper to `aicage-image-base` unless a later design need proves it necessary. Target
images need only their existing SSH and GnuPG clients plus the relevant volume-backed credential sockets; the utility
image owns sidecar behavior when the sidecar path is selected.

## Passphrase handling

When SSH is selected in the terminal configuration UI, its existing confirmation dialog also authorizes SSH setup. On
Linux with a usable host socket, `ssh-add` prompts directly for an encrypted missing key; otherwise the sidecar
prompts directly. Aicage never receives the passphrase. There is no separate setup command.

After a reboot, an empty host service or sidecar receives unencrypted keys before starting a target container.
Encrypted keys require an interactive run to load them directly into the selected service.

A noninteractive invocation never prompts. If an encrypted key is unavailable, it logs a warning and starts the target
container without that identity.

Global and tree configuration preserve the SSH/GnuPG `Auto`/`On`/`Off` inheritance model. `Auto` leaves the global
setting unset or, at a nested scope, does not override its parent; it is not Git detection.

The GnuPG sidecar owns its GnuPG service lifecycle and pinentry behavior. Its noninteractive behavior likewise never
prompts. The socket volumes never contain private keys or passphrases.

## Implementation areas

### `aicage-image-util`

- Build and release `aicage-image-util:credential-agent`, separate from `agent-version`.
- Include OpenSSH and GnuPG tools plus a dispatcher with `ssh` and `gpg` modes.
- Define and test a focused startup and readiness command for each credential socket.
- Publish it through the existing `aicage-image-util` release and image workflow.
- Do not mount host credential material into either socket volume.

### `aicage`

- Prefer direct Linux SSH and Unix GnuPG forwarding; select the relevant sidecar when direct forwarding is
  unavailable. Windows always selects sidecars.
- Add a Docker resource manager for the labelled SSH and GnuPG singleton volumes and sidecars.
- Reuse the established helper-image digest, signature verification, pull, and old-digest cleanup code once for the
  shared credential image.
- Add a short creation/replacement lock.
- Add each enabled protocol's volume mount and agent environment to `DockerRunArgs`.
- Retain the existing read-only target-container mounts for SSH configuration, known-hosts files, and public-key
  files, plus the existing GnuPG public keyring, trust, and configuration mounts; remove only direct private-key and
  host credential-socket mounts.
- Remove direct host credential-socket bind mounts on Windows.

### Tests

- Unit tests for resource inspection, creation, replacement, lock behavior, and protocol-specific socket mount
  arguments.
- Utility-image tests for SSH and GnuPG mode startup, readiness, and credential-loading behavior.
- Linux integration tests: SSH and GnuPG direct forwarding remain functional when host sockets are bind-mountable;
  forced sidecar fallback remains functional for both protocols.
- Windows integration test: Docker Desktop/WSL target container sees the same identities through the volume-backed
  socket; it must not mount a Windows named pipe or require the Windows OpenSSH service.
- GnuPG integration tests: target container signs through the volume-backed GnuPG agent on Linux and Windows without
  private-key mounts.
- Restart integration tests: remove/stop either sidecar and verify the next relevant run recreates it while retaining
  its named volume.
- Test interactive protected-key setup, unprotected-key reload, and noninteractive no-prompt warning behavior.

## Non-goals and constraints

- Never change Windows service state/startup policy.
- Never change Windows key permissions/ACLs.
- Never require an additional host-side credential tool.
- Never mount private keys in target coding-agent containers.
- Do not create per-run sidecars or per-run volumes.
- Do not delete either singleton socket volume during ordinary aicage shutdown.
- Discuss with the user before modifying `aicage-image-base`, especially `scripts/entrypoint.sh`.
