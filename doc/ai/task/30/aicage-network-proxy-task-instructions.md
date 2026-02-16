# Network & Proxy Handling — Implementation Task Instructions for `aicage`

## Metadata

- Author: ChatGPT (OpenAI GPT-5.2)
- Date: 2026-02-16
- Purpose:
  - Provide implementation guidance for a pragmatic and low-complexity networking approach in `aicage`.
  - Intended as task input for an automated coding agent.

---

## Goal

Implement networking behavior that:

1. Works automatically in the majority of environments.
2. Avoids complex proxy-specific logic.
3. Minimizes configuration surface.
4. Produces clear diagnostics when networking fails.

The tool must not attempt to manage or repair user networking configuration.

---

## Design Principles

### 1. Respect Existing Environment Configuration

`aicage` must:

- Respect standard environment variables:
  - `HTTP_PROXY`
  - `HTTPS_PROXY`
  - `ALL_PROXY`
  - `NO_PROXY`
- Not override or rewrite proxy settings automatically.
- Default behavior is “inherit environment”.

No custom proxy configuration format should be introduced initially.

---

### 2. Treat Networking as Three Separate Layers

Implementation must recognize that networking differs across:

1. `aicage` process
2. Docker daemon / BuildKit
3. Containers started by `aicage`

Responsibilities:

- `aicage`:
  - use environment proxy settings for its own HTTP calls.

- Docker daemon:
  - do not attempt automatic configuration.
  - failures should produce clear diagnostics.

- Containers:
  - optionally forward proxy environment variables.

---

### 3. Proxy Environment Forwarding

When launching containers or builds:

If proxy variables exist in the host environment:

Forward the following variables unchanged:

- `HTTP_PROXY`
- `HTTPS_PROXY`
- `ALL_PROXY`
- `NO_PROXY`

This applies to:

- `docker run`
- `docker build` (via `--build-arg`)

Provide a future option to disable forwarding if needed.

---

### 4. Certificate Handling

Requirements:

- Do not disable TLS verification.
- Do not silently accept invalid certificates.

Optional support:

- Allow specifying an additional CA bundle via environment variable:

  ```shell
  AICAGE_CA_BUNDLE=/path/to/certificate.pem
  ```

This affects only `aicage` HTTP calls.

Docker daemon CA handling remains external.

---

### 5. Error Classification

Networking failures must be distinguishable in output:

Detect and classify:

- DNS resolution failure
- TCP connection failure / timeout
- TLS verification failure
- HTTP proxy authentication failure (407)
- HTTP authorization failure (401/403)

Error messages must include:

- target hostname
- operation (GitHub API, registry pull, etc.)

---

### 6. Minimal Debug Command

Introduce a diagnostic command:

```shell
aicage doctor network
```

The command should:**[**

1. Print detected proxy-related environment variables.
2. Attempt simple HEAD/GET requests to:
   - [https://api.github.com](https://api.github.com)
   - [https://ghcr.io](https://ghcr.io)]
   - [https://registry-1.docker.io](https://registry-1.docker.io)
3. Report success or categorized failure.

The command must not modify system configuration.

---

### 7. Explicit Non-Goals

The following are intentionally out of scope:

- Automatic proxy discovery
- NTLM or Kerberos proxy handling
- Docker daemon reconfiguration
- Network auto-repair
- Custom networking abstraction layer

---

## Acceptance Criteria

Implementation is considered complete when:

- `aicage` works unchanged in environments with correctly configured proxy variables.
- Failures produce actionable diagnostics.
- Containers inherit proxy configuration when present.
- No additional configuration is required for normal users.
