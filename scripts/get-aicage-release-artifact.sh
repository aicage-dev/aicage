#!/usr/bin/env bash
set -euo pipefail

# Prerequisites:
# - cosign
# - curl
# - tar

AICAGE_REPO="$1"
TARGET_DIR="$2"

mkdir -p "${TARGET_DIR}"
pushd "${TARGET_DIR}" >/dev/null

echo "Downloading release artifact from 'github.com/aicage/${AICAGE_REPO}' to ${TARGET_DIR} ..." >&2

for artifact in "${AICAGE_REPO}".tar.gz SHA256SUMS SHA256SUMS.sigstore.json; do
  curl -fsSLO \
    --retry 8 \
    --retry-all-errors \
    --retry-delay 2 \
    --max-time 600 \
    "https://github.com/aicage/${AICAGE_REPO}/releases/latest/download/${artifact}"
done

echo "Ensure cosign is available or use cosign image ..." >&2
COSIGN_CMD=cosign
if ! command -v "${COSIGN_CMD}" >/dev/null 2>&1; then
  COSIGN_CMD="docker run --rm -v $(pwd):/work:ro -w /work ghcr.io/sigstore/cosign/cosign:latest"
fi

echo "Verifying signature ..." >&2

${COSIGN_CMD} verify-blob \
  --bundle SHA256SUMS.sigstore.json \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  --certificate-identity-regexp "^https://github\.com/aicage/${AICAGE_REPO}/\.github/workflows/release\.yml@(?:refs/tags/.*|[0-9a-f]{40})$" \
  SHA256SUMS \
   >&2

echo "Verifying checksums ..." >&2

sha256sum -c SHA256SUMS >&2

echo "Unpacking ..." >&2

tar -xzf "${AICAGE_REPO}".tar.gz >&2

echo "Clean up ..." >&2

rm "${AICAGE_REPO}".tar.gz SHA256SUMS SHA256SUMS.sigstore.json >&2

popd >/dev/null

echo "Done downloading release artifact from 'github.com/aicage/${AICAGE_REPO}' to ${TARGET_DIR}" >&2
