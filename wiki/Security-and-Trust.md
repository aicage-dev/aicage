# Security and trust

This page explains four things:

- what `aicage` sends over the network and why
- what `aicage` verifies before using images
- what CI verifies before release
- how much is covered by tests

## Data collection

`aicage` does not collect user data and does not send telemetry.

## Network access

`aicage` still needs normal network access for package and image operations.

<!-- pyml disable md013 -->
| Why                                  | Who connects                                     | Typical target                                                       |
|--------------------------------------|--------------------------------------------------|----------------------------------------------------------------------|
| Version check                        | `aicage` host process                            | `https://pypi.org/pypi/aicage/json`                                  |
| Check if a newer image exists        | `aicage` host process                            | Public registry API (usually GHCR, sometimes Docker Hub)             |
| Get token for registry check         | `aicage` host process                            | Registry token endpoint (anonymous flow for public images)           |
| Pull image layers                    | Docker daemon                                    | Image registry (for built-ins usually `ghcr.io`)                     |
| Verify image signatures              | `aicage` via short-lived cosign container        | Signature data for the image digest                                  |
| Build local images (if needed)       | Docker build steps                               | Package/tool endpoints used by build scripts                         |
| Check agent version for local builds | `aicage` host process or version-check container | Endpoints used by agent `version.sh` (often registries or HTTP APIs) |
| Agent runtime calls                  | Agent in container                               | Endpoints used by that agent/provider                                |
<!-- pyml enable md013 -->

Agents run with their own network behavior and can use mounted credentials.
For built-in agents that are built locally and for custom local agents, `aicage` runs the agent `version.sh` check.
Those checks can call registries or HTTP APIs, depending on the script.

## Image trust

Before `aicage` pulls built-in remote images, it verifies signatures.

Checks include:

- image digest
- expected signer identity
- expected OIDC issuer (`https://token.actions.githubusercontent.com`)

Runtime note: local runtime enforces signature checks. It does not run full SLSA verification locally.

### Docker rootless mode

- `aicage` supports hosts that use a [rootless Docker](https://docs.docker.com/engine/security/rootless/) daemon. 
- This can reduce the risk of full host-root compromise compared with a rootful Docker daemon, including when using
  `aicage --docker`.
- It does not meaningfully protect files or other data already accessible to your host user.

## CI trust checks before release

Image release pipelines run these checks before publishing:

- build for amd64 and arm64
- smoke tests
- sign images
- verify signatures
- check provenance presence

Non-redistributable agent images are also smoke-tested in CI before release.

## Test coverage

`aicage` release CI runs:

- unit tests with coverage
- integration tests for real Docker runs for most use cases
- dedicated proxy integration scenarios

Recent coverage runs:

- unit-test coverage (`pytest --cov=src --cov-report=term-missing`): 96%
- integration/E2E coverage: 53%
  command:
  `AICAGE_RUN_INTEGRATION=1 AICAGE_RUN_PROXY_INTEGRATION=1 \
  pytest -m integration --cov=src --cov-report=term-missing`

These percentages are from separate runs and are not additive.
