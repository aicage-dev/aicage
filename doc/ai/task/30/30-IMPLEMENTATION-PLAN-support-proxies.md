# Task 30 Implementation Plan (Updated)

## Options overview

### Option 1: Functional proxy forwarding only

- Forward uppercase proxy environment variables from host into:
  - runtime `docker run`
  - `docker build` via `--build-arg`
  - helper `docker run` calls (for version checks)
- Keep existing error handling and diagnostics unchanged.

### Option 2: Functional forwarding + better diagnostics (selected)

- Includes everything from Option 1.
- Adds lightweight network failure classification at existing HTTP call sites.
- Improves messages/logs with operation + target host + classified failure type.
- Keeps current control flow (no broad exception architecture changes).

### Option 3: Expanded UX/debug features

- Includes Option 2 plus larger troubleshooting surface, e.g. dedicated doctor/debug command(s).
- Intentionally not selected to keep implementation small and focused.

## Scope decisions

- Follow option 2 (functional proxy forwarding + better diagnostics).
- Do not add `aicage doctor` commands.
- Respect only uppercase proxy environment variables:
  - `HTTP_PROXY`
  - `HTTPS_PROXY`
  - `ALL_PROXY`
  - `NO_PROXY`
- Do not parse or inspect user-provided docker argument strings.
- Do not implement deduplication logic.

## Step 1: Add a private proxy helper module

Create `src/aicage/runtime/_proxy.py`.

Provide focused helper functions:

- `proxy_env_vars_from_host() -> list[EnvVar]`
- `proxy_build_args_from_host() -> list[str]`
- `proxy_run_env_args_from_host() -> list[str]`

Behavior:

- Read only uppercase host environment variables listed above.
- Return empty outputs when variables are not set.
- No normalization, no lowercase support, no deduplication.

## Step 2: Forward proxies to main runtime container

Update `src/aicage/runtime/run_plan.py`.

Change `build_run_args(...)` so `DockerRunArgs.env` is built as:

- existing `config.env`
- plus `proxy_env_vars_from_host()`

Keep all other logic unchanged.

## Step 3: Forward proxies to all docker builds

Update `src/aicage/docker/build.py`.

For each command in:

- `run_build(...)`
- `run_extended_build(...)`
- `run_custom_base_build(...)`

append `proxy_build_args_from_host()` to the `docker build` argument list.

No other behavior changes.

## Step 4: Forward proxies for version-check helper container

Update `src/aicage/docker/run.py`.

In `run_builder_version_check(...)`, append `proxy_run_env_args_from_host()` into the `docker run` command
construction.

No other behavior changes.

## Step 5: Add lightweight network classification helpers

Create `src/aicage/_network.py` (private module).

Add minimal helpers to classify and format network failures:

- classify DNS resolution failures
- classify connection/timeout failures
- classify TLS/certificate failures
- classify proxy auth failures (`HTTP 407`)
- classify auth failures (`HTTP 401`/`HTTP 403`)
- generic fallback (`http_error`, `unknown`)
- extract target host from URL for diagnostics

No broad exception architecture changes.

## Step 6: Improve diagnostics at existing HTTP call sites

Apply helper usage without changing core control flow.

### `src/aicage/cli/_version_check.py`

- On fetch failures, keep current behavior (`None` returned).
- Improve warning log text with:
  - operation
  - target host
  - classified failure type

### `src/aicage/registry/digest/_http.py`

- On URL failures, keep current return `(None, {})`.
- Add warning log with operation + host + classified type.

### `src/aicage/registry/digest/_auth.py`

- On token request failures, keep current return `None`.
- Add warning log with operation + host + classified type.

### `src/aicage/docker/_registry_api.py`

- Keep raising `RegistryDiscoveryError` on request failure.
- Enrich raised message with operation + host + classified type.

## Step 7: Tests to add/update

### New tests

- `tests/aicage/runtime/test__proxy.py`
  - verifies uppercase env capture
  - verifies build-arg shaping
  - verifies docker-run `-e` flag shaping

- `tests/aicage/test__network.py`
  - verifies classification behavior for key failure classes

### Update existing tests

- `tests/aicage/runtime/test_run_plan.py`
  - verify proxies are appended to runtime env

- `tests/aicage/docker/test_build.py`
  - verify build commands include proxy `--build-arg` entries

- `tests/aicage/docker/test_run.py`
  - verify `run_builder_version_check` includes proxy `-e` entries

- adjust network-call tests only where message/assertion expectations change:
  - `tests/aicage/cli/test__version_check.py`
  - `tests/aicage/docker/test__registry_api.py`
  - `tests/aicage/registry/digest/test__http.py`
  - `tests/aicage/registry/digest/test__auth.py`

## Step 8: Validation

Run with existing virtualenv:

```bash
source .venv/bin/activate
pytest --cov=src --cov-report=term-missing
scripts/lint.sh
```

Fix issues in a loop until both commands pass.

## CI integration test plan (proxy end-to-end)

Goal: validate not only env propagation, but that traffic actually traverses a real proxy and succeeds.

### Approach

- Add a proxy-enabled workflow leg in GitHub Actions.
- Reuse selected existing integration tests that already execute image pull/build/run flows.
- Run the tests against a controlled Docker daemon in CI (DinD), not only the host daemon.
- Assert both:
  - operation success
  - proxy access logs contain expected traffic

### Why DinD is required

Docker daemon pull/build networking is a separate layer from:

- `aicage` process HTTP calls
- container runtime env forwarding

To validate daemon-level proxy behavior (registry pull and auth endpoints), tests must target a daemon whose proxy
configuration is known and controlled by the workflow.

### Workflow shape

1. Start a real proxy service container (for example Squid) in the workflow.
2. Start Docker-in-Docker service with daemon proxy env configured (`HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`).
3. Point test execution to DinD via `DOCKER_HOST`.
4. Set proxy env in the test process (`HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, `NO_PROXY`).
5. Run selected integration tests.
6. Parse proxy logs and assert expected targets/requests were proxied.

### Assertions by layer

- Host-side HTTP calls:
  - calls succeed
  - proxy logs show host requests
- Docker build (`RUN` network access):
  - build succeeds
  - proxy logs show build-time fetch requests
- Docker run (agent/runtime network access):
  - run succeeds
  - proxy logs show runtime fetch requests
- Docker daemon registry pull/auth:
  - pull/build that requires base image retrieval succeeds
  - proxy logs show registry/auth traffic (for example `ghcr.io`, `registry-1.docker.io`, token endpoints)
