# Task 29 — Failsafe continue when possible

## Problem description

Currently `aicage` fails to run without working internet connection (mostly to GitHub docker image registry).

While this is by design, one can imagine scenarios where this can get in the way of users like:

- all aicage images are locally present and connection to the LLM is on local Ollama or on local network without full
  connection to the internet.
- user totally builds his own images with:
  - custom base image
  - agent installation custom or possible (npm packages allowed on the netowrk)
- maybe other scenarios

### Problem example

One example I found was with custom-agent `vibe` (see `../aicage-custom-samples/agents/vibe`) and the builtin remote
base image `alpine`. The images below were all present locally (maybe not the most recent from online) so `aicage vibe`
should work. But in effect it choked with error message:  
`Failed to resolve remote digest for ghcr.io/aicage/aicage-image-base:alpine.`  

## Thin line approach

Catching such errors and letting `aicage` continue must be done in a defensive manner - it's walking a thin line.  
What we don't want is to allow too much pass through or we risk hiding real problems which might bite us down the line.

So when we allow such errors to pass, then each case must have a well-defined scenario, like in the example case for
'remote digest lookup of base image fails':
- if a local ghcr.io/aicage/aicage-image-base:alpine is present, then continue by using that as base-image
- otherwise if no local base image `alpine` is present but next stage image `aicage:vibe-alpine` is, then continue
  by using that as agent-image

Continue means: log it as warning and possibly even with output to user. And the above 2 aproaches must not happen at
one place in the code. One could also imagine just continuing on error of digest lookup for base image and then look at
the situation again in next stage. But it's a thin line as I said.

## Identify issues

I gave you one example only, you shall find more as I did not test all scenarios.

The only other problem I detected was with locally built builtin agent `claude` which seems to hang forever.  
With `claude` I think the problem might be the agent-version check with `config/agent-build/agents/claude/version.sh`.  
When I ran the command in that script while being offline then it also seemed to hang forever.

Again, not something I see an easy fix for which is worth it. I also do not know how those agents would behave when
running bare-metal on offline host. I know at least some agents (`codex` for example) run update check and tell user
when there is a new version of the agent.

## Analyze detected issues

So for detected issues I want an analysis by you including how difficult it's to prevent for each case plus an estimate
if working around it is worth it. If so, propose feasible solutions.

## Task workflow

- Don’t forget to read `AGENTS.md` and `doc/python-test-structure-guidelines.md` and respect those rules.
- Always use the existing venv.

You shall follow this order:

1. Read documentation and code to understand the task.
2. Ask me questions if something is not clear to you.
3. Present me with an implementation solution; this needs my approval.
4. Implement the change autonomously including a loop of running-tests, fixing bugs, running tests.
5. Run linters, use `scripts/lint.sh` with active venv.
6. Present me the change for review.
7. Interactively react to my review feedback.
8. Do not commit any changes unless explicitly instructed by the user.
