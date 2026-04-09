#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/debug/show-sbom.sh <image> [--platform <platform>]

Print the SPDX SBOM attached to a published image.

Options:
  --platform <value>  Platform to print (default: linux/amd64)
  -h, --help          Show this help and exit

Examples:
  scripts/debug/show-sbom.sh node:alpine
  scripts/debug/show-sbom.sh node:alpine --platform linux/arm64
USAGE
  exit 1
}

die() {
  echo "[show-sbom] $*" >&2
  exit 1
}

IMAGE_REF=""
PLATFORM="linux/amd64"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform)
      [[ $# -ge 2 ]] || die "--platform requires a value"
      PLATFORM="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    --)
      shift
      break
      ;;
    -*)
      die "Unknown option '$1'"
      ;;
    *)
      if [[ -n "${IMAGE_REF}" ]]; then
        die "Unexpected extra argument '$1'"
      fi
      IMAGE_REF="$1"
      shift
      ;;
  esac
done

[[ -n "${IMAGE_REF}" ]] || usage
command -v docker >/dev/null 2>&1 || die "docker is required"
command -v jq >/dev/null 2>&1 || die "jq is required"

SBOM_JSON="$(docker buildx imagetools inspect "${IMAGE_REF}" --format '{{ json .SBOM }}')"

if [[ "${SBOM_JSON}" == "{}" || "${SBOM_JSON}" == "null" ]]; then
  die "No SBOM attached to image '${IMAGE_REF}'. It may have been built without sbom attestation."
fi

AVAILABLE_PLATFORMS="$(
  printf '%s\n' "${SBOM_JSON}" | jq -r 'keys | join(", ")'
)"

printf '%s\n' "${SBOM_JSON}" \
  | jq -e --arg platform "${PLATFORM}" '
      if .[$platform] == null then
        error("No SPDX SBOM found for platform " + $platform)
      end
      | .[$platform].SPDX
    ' || die "No SPDX SBOM found for platform '${PLATFORM}'. Available platforms: ${AVAILABLE_PLATFORMS}"
