# Update behavior

`aicage` keeps images current by checking versions and digests at runtime and in CI.

## Summary

- Base images are rebuilt in CI on a schedule or manually.
- Prebuilt agent images are rebuilt in CI when the agent version or base image changes.
- Images that must be built locally are rebuilt when the agent version or base image changes.
- Custom agents and extensions are rebuilt locally when their inputs change.
- `aicage` cleans up superseded image digests and source tags after pulls, runs, and local rebuilds to reduce local
  image ballast.

## Update triggers matrix

| Item                    | Trigger                                 | Built on |
|-------------------------|-----------------------------------------|----------|
| Base image              | Scheduled                               | CI       |
| Custom base image       | Upstream digest of `from_image` changes | Client   |
| Prebuilt agent image    | Agent version or base image change      | CI       |
| Build-local agent image | Agent version or base image change      | Client   |
| Custom agent image      | Agent version or base image change      | Client   |
| Extension image         | Extension changes or base/agent changes | Client   |

## What triggers local rebuilds

Local rebuilds happen when any of these change:

- The agent version (from `version.sh`).
- The base image digest (pulled from the registry).
- The extension contents.

This is automated; you do not need to manually manage image rebuilds.
