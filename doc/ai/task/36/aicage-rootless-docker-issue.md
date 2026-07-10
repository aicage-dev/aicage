# Support Rootless Docker

## Summary

Investigate and add first-class support for running AICage with
**rootless Docker**.

The goal is to reduce the impact of giving an AI agent access to the
Docker socket while preserving AICage's existing developer experience.

## Motivation

Today AICage is primarily designed for rootful Docker.

The current startup logic:

-   passes the host username, UID, GID and HOME to the container
-   creates a matching user inside the container
-   switches to that user before starting the agent
-   ensures files written to bind mounts are owned by the host user

When using rootless Docker, the security model changes:

-   the Docker daemon runs as the invoking host user instead of host
    root
-   access to the Docker socket no longer implies host-root privileges
-   compromise of the Docker daemon is generally limited to the
    privileges of the host user

This makes rootless Docker attractive for running AI coding agents.

## Goals

-   Detect whether Docker is running in rootless mode.
-   Preserve the existing AICage workflow where possible.
-   Preserve correct ownership of files written to bind-mounted
    directories.
-   Preserve HOME/path behaviour.
-   Minimize changes required by users.

## Investigation

Things to verify:

-   Does the current runtime-user setup still make sense under rootless
    Docker?
-   Is dynamic user creation still needed?
-   Which UID inside the container should actually execute the agent?
-   Does bind-mounted file ownership remain correct?
-   Which Docker features used by AICage are unavailable or behave
    differently in rootless mode?
-   Is a separate execution mode required, or can AICage adapt
    automatically?

## Acceptance Criteria

-   AICage works correctly with both rootful and rootless Docker.
-   Files created in bind mounts remain editable by the host user.
-   Existing functionality is not regressed.
-   Any rootless limitations are documented.
