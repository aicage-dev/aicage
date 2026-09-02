# Hermes Review: aicage

Entry point for the whole-repository audit of `aicage`.

Files:
- `architecture.md` — architecture summary, execution flow, inspected scope
- `findings.md` — detailed findings with severity, confidence, location, explanation, fix
- `ci_release.md` — CI/build/release/testing observations
- `inconsistencies.md` — cross-repository/doc inconsistencies, including `../aicage.wiki`

Run `pytest --cov=src --cov-report=term-missing` from the repo root to verify current test state.
