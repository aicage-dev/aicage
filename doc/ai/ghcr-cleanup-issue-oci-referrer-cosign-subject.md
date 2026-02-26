# ghcr-cleanup-action deletes OCI referrer-based Cosign signature bundles for still-referenced platform manifests

## Summary

`dataaxiom/ghcr-cleanup-action@v1.0.16` appears to delete OCI referrer-based Cosign signature bundle artifacts
(`application/vnd.dev.sigstore.bundle.v0.3+json`) even when their subject digest is still referenced by kept images.

In my case, the subject was an architecture-specific manifest digest that is still referenced by tagged multi-arch
indexes. The cleanup run removed the signature bundle anyway.

## Why this looks incorrect

The README says the cleanup algorithm removes child images from the working filter set, including referrers and cosign
images.

- README (Cleanup Algorithm):
  - "Remove all child images from the working filter set (including referrers and cosign images)."

Given that wording, I would expect Cosign referrer artifacts attached to still-referenced child manifests to be retained.

## Reproduction scenario

1. Use a package with multi-arch images and Cosign signatures on both index and platform digests.
1. Keep latest tags via regex (for example `exclude-tags` with `use-regex: true`) and enable `delete-untagged: true`.
1. Run `dataaxiom/ghcr-cleanup-action@v1.0.16` in `dry-run` first.
1. Observe planned deletions include package versions with:
   - `config.mediaType: application/vnd.oci.empty.v1+json`
   - `artifactType: application/vnd.dev.sigstore.bundle.v0.3+json`
   - `subject.digest: sha256:<platform-manifest-digest>`
1. Run without dry-run and verify those signature bundles are deleted.

## Concrete observation

Deleted artifact (example):

- digest: `sha256:67afb7d62054aabdd0b1594df10c6a5ef975399be3270e69d6d5477956eeaf52`
- artifactType: `application/vnd.dev.sigstore.bundle.v0.3+json`
- subject.digest: `sha256:d7b294534d8093ae681641fc92278544e4a7f51d89fc441d5e8979b5e37f1bb4`

The subject digest had no direct tags, but it was still referenced by kept multi-arch tags (indirectly via index
manifests).

## Expected behavior

If a digest is still reachable from kept images (for example as a child manifest of a kept multi-arch index), OCI
referrer artifacts for that digest (including Cosign signature bundles) should not be deleted.

## Actual behavior

OCI referrer-based Cosign bundles were selected and deleted despite their subject digest still being referenced by kept
images.

## Possible cause

The current implementation appears to handle referrers primarily using tag-based `sha256-...` heuristics rather than a
full OCI subject/referrers graph traversal. This likely misses some OCI referrer relationships and can classify valid
referrer artifacts as deletable.

## Request

Please confirm whether this is a bug in `v1.0.16` and whether a fix can be made to preserve OCI referrers whose
subjects are still referenced by retained manifests.
