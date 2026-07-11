# Task 37 Proposal

## Goal

Introduce a new user configuration UI without destabilizing the existing config and run flow.

The first step is not a direct Textual rewrite. The first step is an internal refactor that moves current
prompt-driven config handling to a single in-memory draft flow for one invocation of `aicage <agent>`.

This keeps the current behavior available while creating a clean seam for a future overview/edit UI.

## Current problem

Current configuration handling is spread across several modules:

- image selection asks for base and extensions
- runtime config handling persists docker args and shares
- mount support prompts persist mount preferences

This works for a linear first-run questionnaire, but it is a poor fit for an overview-based UI where a user can:

- inspect all values first
- enter a subsection
- change values multiple times
- remove previously persisted values
- cancel without partial writes
- accept the final result with a single key

With the current structure, introducing such a UI would either:

- write partial user decisions to disk while editing is still in progress
- or spread temporary state handling across even more modules

## Proposed approach

Add a private in-memory config draft model for the current invocation.

Behavior:

1. Load current project config and CLI inputs.
2. Build a draft containing the editable per-project and per-agent state.
3. Let the active UI mutate only the draft.
4. Persist the draft to the config file once the user confirms.
5. Use the finalized result to build Docker run state.

Important constraints:

- no new persisted "session" concept
- no new config file format unless needed by actual feature work
- no immediate removal of the current prompt flow
- no default switch to a new UI in the first implementation

## What this gains us

### Atomic config writes

The config file is written once after confirmation.

This gives clear behavior for:

- cancel
- back-and-forth edits
- section-based editing
- Enter to accept all

### Cleaner separation

The flow becomes easier to reason about:

- draft construction
- draft editing
- persistence
- runtime resolution

Each concern can be tested separately.

### Safe migration path

The current prompt flow can remain available while a new overview UI is developed and tested.

Both UI paths can operate on the same draft and persist through the same code path.

### Better support for removing config

The current flow is largely add-only for shares and related extras.

The draft model allows temporary removal and re-adding during editing before any final write.

## Phased implementation

### Phase 1: Internal draft refactor

Scope:

- introduce private draft datatypes and mapping logic
- move current prompt-driven behavior to operate on the draft
- keep the current CLI behavior and prompt UX as the default
- keep persistence as one final write

Expected result:

- no intended user-visible behavior change
- better test coverage around config assembly and persistence

### Phase 2: Experimental overview UI

Scope:

- add a new overview-based config UI on top of the draft
- show current values for:
  - base
  - agent
  - extensions
  - shares
  - extras
- support Enter to accept and continue
- support editing at least:
  - base
  - extensions
  - shares
  - extras/mount-related persisted settings

Expected result:

- new UI available behind an explicit CLI gate
- old prompt flow still available

### Phase 3: Iterate and promote

Scope:

- refine UX
- close feature gaps
- extend tests
- decide whether Textual should replace or back the experimental UI
- switch the default once stable

Expected result:

- new UI becomes the primary path
- old prompt-only path can later be removed

## UI gating recommendation

Do not switch the new UI on by default in the first version.

Recommended temporary gating:

- add an explicit CLI option for the new UI

Candidate shapes:

- `--config-ui`
- `--ui=overview`
- `--ui=textual`

Preferred direction:

- start with a generic UI selector if multiple UIs are plausible
- otherwise start with `--config-ui` and keep it simple

This makes rollout safer and keeps fallback behavior obvious.

## Textual recommendation

Do not make Textual the first hard dependency of the refactor step.

Reason:

- the hardest problem right now is not rendering widgets
- the hardest problem is consolidating temporary editable state and final persistence

Once the draft flow exists, Textual becomes much easier to evaluate and integrate because the UI layer can stay
focused on editing the draft rather than owning persistence behavior.

## Testing approach

### Phase 1 tests

Add unit tests for:

- building a draft from stored config and CLI input
- applying current prompt choices to the draft
- persisting final draft state back to project config
- preserving current default behavior

Keep or adapt existing tests around:

- base selection
- extension selection
- docker arg persistence
- share persistence
- mount preference persistence

### Phase 2 tests

Add tests for:

- overview accept flow
- editing a persisted value
- removing a persisted value
- cancel path with no file change
- CLI args pre-filling draft state

## Likely code impact

Primary areas:

- `src/aicage/config/runtime_config.py`
- `src/aicage/registry/image_selection/*`
- `src/aicage/runtime/prompts/*`
- `src/aicage/runtime/docker_args/*`
- `src/aicage/cli/_parse.py`

New code should remain private by default unless it is clearly used across module boundaries.

## Initial implementation recommendation

Start with Phase 1 only.

That keeps the first change:

- reviewable
- testable
- low-risk
- useful on its own

Then add the new UI behind a flag in a second step.
