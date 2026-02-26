# GHCR Artifact Analysis – Cosign Signature Bundles

## Context

During cleanup of the GitHub Container Registry (GHCR) package:

`ghcr.io/aicage/aicage`

The following entry appeared:

```text
deleting package id: 705946143
digest: sha256:67afb7d62054aabdd0b1594df10c6a5ef975399be3270e69d6d5477956eeaf52
application/vnd.oci.empty.v1+json
```

This raised the question: What exactly is this artifact?

---

## Inspection of the Artifact

Command used:

```bash
regctl manifest get   ghcr.io/aicage/aicage@sha256:67afb7d62054aabdd0b1594df10c6a5ef975399be3270e69d6d5477956eeaf52 \
  --format raw-body \
  | jq .
```

Key parts of the output:

```json
{
  "artifactType": "application/vnd.dev.sigstore.bundle.v0.3+json",
  "config": {
    "mediaType": "application/vnd.oci.empty.v1+json",
    "artifactType": "application/vnd.dev.sigstore.bundle.v0.3+json"
  },
  "layers": [
    {
      "mediaType": "application/vnd.dev.sigstore.bundle.v0.3+json"
    }
  ],
  "subject": {
    "digest": "sha256:d7b294534d8093ae681641fc92278544e4a7f51d89fc441d5e8979b5e37f1bb4"
  }
}
```

### Interpretation

This is:

- A **cosign signature bundle artifact**
- Stored as an OCI artifact
- With empty OCI config (`application/vnd.oci.empty.v1+json`)
- Whose subject digest is:

```text
sha256:d7b294534d8093ae681641fc92278544e4a7f51d89fc441d5e8979b5e37f1bb4
```

---

## What Is `sha256:d7b294...`?

Important:

- `sha256:d7b294534d8093ae681641fc92278544e4a7f51d89fc441d5e8979b5e37f1bb4`
- has **no direct tags**
- `regctl tag ls` will not show it
- it is an **arch-specific image manifest**

To determine which tags indirectly reference that digest:

```bash
IMG=ghcr.io/aicage/aicage
CHILD=sha256:d7b294534d8093ae681641fc92278544e4a7f51d89fc441d5e8979b5e37f1bb4

regctl tag ls "$IMG" | while read -r T; do
  regctl manifest get "$IMG:$T" --format raw-body 2>/dev/null   | jq -e --arg d "$CHILD" '
      (.manifests? // []) | any(.digest == $d)
    ' >/dev/null && echo "$T"
done
```

### Result

```text
opencode-1.2.14-fedora-0.9.18
opencode-1.2.14-fedora-0.9.18-arm64
opencode-1.2.14-fedora-0.9.18-arm64-test
opencode-fedora
opencode-fedora-arm64
```

This computation took several minutes due to full tag enumeration and manifest inspection.

---

## What This Means

- `sha256:d7b294...` is an **arch-specific image manifest**
- It has **no direct tags**
- It is referenced by one or more **multi-arch index manifests**
- The tags are attached to the **index**, not the arch-specific child
- The artifact `sha256:67afb7...` is a **cosign signature bundle**
- It signs the arch-specific child manifest

---

## Structural Model

```text
Tag (e.g. opencode-fedora)
        ↓
Multi-arch index (manifest list)
        ↓
Platform-specific manifest (sha256:d7b294...)
        ↓
Cosign signature bundle artifact
```

---

## Conclusion

The cleanup target:

```text
application/vnd.oci.empty.v1+json
```

was:

- NOT an image
- NOT a manifest list
- A cosign signature bundle artifact
- Signing an arch-specific child image
- That child image has **no direct tags**
- It is indirectly referenced by tagged multi-arch indexes

Deleting this artifact:

- Does NOT remove the image
- Does NOT break pulling the image
- DOES remove the signature for that digest
- Causes `cosign verify` for that subject digest to fail unless re-signed

This behavior is expected when using multi-arch images with cosign and OCI referrers in GHCR.
