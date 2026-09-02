# CI / Release / Testing Observations

Verified from repo files only; this does not inspect actual GitHub Actions run results.

## CI workflows

- `lint-and-test.yml` runs on a Python version matrix and calls `scripts/lint.sh`, `pytest --cov=src --cov-report=term-missing`, and schema validation.
- `change-validation.yml` gates PRs/pushes to `main` with lint/test and optional integration tests.
- `ci_lint.yml` runs MegaLinter with autofix PR creation and stale-fix-PR cleanup.
- `release.yml` verifies the tagged commit is on `origin/main`, runs the test suite, then publishes to PyPI.
- Integration workflows exist for Linux, macOS, Windows, and proxy scenarios.

## Release/publishing

- Release uses PyPI trusted publishing via `id-token: write` + `pypa/gh-action-pypi-publish`.
- `release.yml` installs cosign, verifies the cosign image, and rewrites `_COSIGN_IMAGE_DIGEST` in `src/aicage/constants.py` via `sed`.
- `scripts/get-aicage-release-artifact.sh` references `SHA256SUMS.sigstore.json` and `cosign verify-blob`, suggesting release-artifact Sigstore verification exists outside this repo's CI.
- `scripts/debug/show-sbom.sh` can display an image SBOM if present, but there is no in-repo SBOM generation step in `release.yml`.

## Tooling/lint

- `.mega-linter.yml` disables `PYTHON_MYPY`, `PYTHON_PYLINT`, and `REPOSITORY_DEVSKIM`.
- `scripts/lint.sh` still runs `mypy`, `pylint`, and `flake8`; CI therefore enforces those checks even though MegaLinter skips them.
- MegaLinter's `ACTION_ZIZMOR_UNSECURED_ENV_VARIABLES` exempts `GITHUB_TOKEN`, which is expected for workflows that need it.

## Testing

- `pytest --co` collects 901 tests; local run shows 860 passed, 41 skipped.
- Integration tests are opt-in via `AICAGE_RUN_INTEGRATION=1`.
- `DEVELOPMENT.md` notes Linux-only full-suite assumptions and macOS/Windows caveats.

## Notes

- Earlier drafts mentioned Lychee and SBOM/provenance as gaps; that was overreaching.
  - `lychee.toml` is consistent with MegaLinter link checking.
  - `show-sbom.sh` exists for inspection, but SBOM attestation is not visibly generated in this repo.
  - Package-level provenance is via PyPI trusted publishing; image-level cosign verification is present for runtime images.
