# Task 35: Base-image architecture restrictions

## Goal

Add architecture-aware base-image support across the `aicage` project family so bases can declare
which CPU architectures they support.

Primary driver:

- Arch Linux base images are `amd64` only.

Required outcome:

- `amd64`-only bases are built only for `amd64`.
- agent-image pipelines consume that restriction correctly.
- `aicage` does not offer or accept unsupported bases on host architectures that are not supported.

## Approved scope

This task introduces base-level architecture metadata.

Chosen representation:

```yaml
architectures:
  - amd64
```

Not chosen:

```yaml
platforms:
  - linux/amd64
```

Reason:

- the current problem is architecture support, not OS support
- using `linux/amd64` would implicitly encode an OS policy
- that could accidentally change Windows behavior
- this task must not introduce an explicit Windows prohibition without separate analysis

## Intended behavior

- Architecture filtering is based on CPU architecture only.
- Existing bases default to supporting both `amd64` and `arm64` when the field is omitted.
- Arch Linux is declared as `amd64` only.
- Windows and macOS hosts are not newly prohibited by this task.
- `aicage` should filter base choices by host architecture.

Examples:

- `amd64` host: Arch may be offered.
- `arm64` host: Arch must not be offered.

## Repositories in scope

### `aicage-image-base`

Source of truth for builtin base metadata.

Needed changes:

- add `architectures` to base schema
- mark Arch base as `amd64` only
- make base-image CI build and publish only declared architectures
- keep release artifacts carrying the metadata unchanged

### `aicage-image`

Consumes released base metadata and builds agent images.

Needed changes:

- combine existing agent/base exclusion rules with base architecture support
- generate build matrices only for supported architectures
- refresh/rebuild checks must only require architectures supported by a base

Non-goal:

- no new per-agent architecture exclusion field unless a real use case appears

### `aicage`

Python CLI/runtime running on the user machine.

Needed changes:

- extend base metadata model with `architectures`
- detect host architecture
- filter base options and validation by host architecture
- apply the same schema to builtin bases and custom bases

### `aicage-custom-samples`

Must use the same base schema as builtin bases.

Needed changes:

- add `architectures` support to sample base definitions
- keep one schema model only

### `aicage` custom base samples

The sample custom bases shipped in this repo must stay aligned with the same schema.

Needed changes:

- update sample custom base definitions under `doc/sample/custom/base-images/`
- update schema validation coverage for those samples if required

## Constraints

- Keep the solution simple.
- Do not introduce a second schema for custom bases.
- Do not use this task to define Windows container support policy.
- Keep shell-side and Python-side compatibility logic symmetric.

## Main risks

- compatibility logic currently exists in both shell and Python, so partial updates can create
  inconsistent behavior
- CI currently assumes that every valid base exists for both `amd64` and `arm64`
- defaults must preserve current behavior for existing multi-arch bases

## Suggested implementation order

1. Update `aicage-image-base` to define and publish architecture-restricted bases correctly.
2. Update `aicage-image` to consume base architecture metadata in matrices and refresh checks.
3. Update `aicage` to enforce architecture-aware base filtering at runtime and for custom bases.
4. Update `aicage-custom-samples` and in-repo sample custom bases to the shared schema.
5. Add targeted tests for the Arch `amd64`-only case.

## Test intent

Key regression expectations:

- multi-arch bases keep working unchanged
- Arch is available on `amd64`
- Arch is hidden or rejected on `arm64`
- release/build/refresh pipelines do not expect missing `arm64` artifacts for Arch
