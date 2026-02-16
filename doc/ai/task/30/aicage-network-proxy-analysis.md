# Network & Proxy Scenarios Analysis for `aicage`

## Metadata

- Author: ChatGPT (OpenAI GPT-5.2)
- Date: 2026-02-16
- Requested by: Maintainer of the `aicage` project
- Task:
  - Provide a realistic analysis of networking and proxy scenarios relevant to a CLI tool that:
    - performs HTTP(S) REST calls to GitHub and container registries
    - interacts with Docker for image pulls and builds
    - launches containers that may perform their own network operations
  - The goal is pragmatic coverage of real-world environments rather than theoretical networking completeness.

---

## Purpose of this Document

This document describes networking situations that realistically occur for users of developer tooling and container
workflows. The intent is to identify where failures originate so implementation decisions can reduce support burden and
improve diagnostics.

This is not a networking tutorial.

---

## Networking Layers Relevant to `aicage`

Networking behavior differs across three independent layers:

### Layer 1 — `aicage` Process

Direct HTTP(S) requests performed by the CLI itself:

- GitHub REST API (`api.github.com`)
- Container registries (`ghcr.io`, `docker.io`)
- Token and blob endpoints

Characteristics:

- Uses host environment variables.
- Uses host certificate trust.
- Usually behaves like `curl`.

---

### Layer 2 — Docker Daemon / BuildKit

Responsible for:

- Pulling images
- Pushing images
- Resolving registry authentication
- Downloading build dependencies

Important property:

- Docker daemon configuration is independent from the shell environment.
- Proxy configuration may differ from the CLI environment.

---

### Layer 3 — Containers (Runtime or Build Stage)

Network activity inside containers:

- Package managers (`apt`, `dnf`, `pip`, etc.)
- Downloading dependencies
- Accessing internal services

Characteristics:

- Environment variables must be passed explicitly.
- Certificate trust differs from host.

---

## Realistic Network Scenarios

### 1. Explicit HTTP(S) Proxy

Typical environment:

- Corporate network
- Proxy defined via:
  - `HTTP_PROXY`
  - `HTTPS_PROXY`
  - `NO_PROXY`

Common failures:

- Applications ignoring proxy variables fail to connect.
- Docker daemon not configured for proxy while CLI is.

Frequency:

- Very common.

---

### 2. TLS Interception (Corporate MITM Proxy)

Typical environment:

- Corporate proxy terminates TLS and re-signs traffic.
- Corporate root CA installed in OS/browser only.

Common failures:

- Certificate verification errors.
- Docker pulls fail while browser works.

Root cause:

- CLI tools and containers do not trust corporate CA by default.

Frequency:

- Extremely common in enterprise environments.

---

### 3. Proxy Authentication Required

Typical environment:

- Proxy requires authentication (Basic, NTLM, Kerberos).

Common failures:

- HTTP 407 responses.
- CLI tools cannot authenticate automatically.

Notes:

- Often works in browsers due to OS integration.
- Difficult to solve generically in CLI tools.

---

### 4. Split Configuration Between Host, Docker, and Containers

Typical environment:

- Host connectivity works.
- Docker daemon lacks proxy configuration.
- Builds fail inside Dockerfiles.

Common failures:

- GitHub API reachable but `docker pull` fails.
- Image pull succeeds but build steps fail.

Frequency:

- One of the most common real-world issues.

---

### 5. Incorrect or Missing `NO_PROXY`

Typical environment:

- Internal registries or LAN services exist.

Common failures:

- Requests incorrectly routed through proxy.
- Local services unreachable.

Examples:

- `localhost`
- LAN IP ranges
- internal registry hostnames

---

### 6. Firewall / Allowlist Environments

Typical environment:

- Only specific domains allowed outbound.

Common failures:

- Authentication works but layer downloads fail.
- Intermittent registry failures.

Cause:

- Different registry endpoints blocked.

---

### 7. DNS Differences Between Host and Containers

Typical environment:

- VPN or internal DNS only configured on host.

Common failures:

- Host resolves names correctly, containers do not.
- Resolution succeeds but routing fails.

---

### 8. SOCKS Proxies / Developer Setups

Typical environment:

- SSH tunnels or local SOCKS proxies.

Common failures:

- Partial support depending on HTTP implementation.
- Docker daemon often unsupported directly.

---

### 9. Windows / WSL / Docker Desktop Differences

Typical environment:

- Multiple proxy configurations.
- Different certificate stores.

Common failures:

- Works in browser but fails in WSL or containers.

---

## Key Observations

1. Most failures originate from configuration differences between layers.
2. Users typically cannot distinguish TLS, proxy, or DNS failures.
3. Clear error reporting is more valuable than automatic network handling.
4. Minimal, predictable behavior reduces support complexity.

---

## Summary

`aicage` should assume that networking environments vary widely and avoid complex automatic behavior. The main
responsibility of the tool should be:

- respecting existing environment configuration,
- forwarding relevant configuration where appropriate,
- and providing clear diagnostics when failures occur.
