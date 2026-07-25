# Custom base images

Custom base images let you build and update base layers locally. They live under
`~/.aicage-custom/base-images/` and show up alongside built-in bases during selection.

If a custom base name matches a built-in base name, the custom base overrides it.

## Directory layout

```text
~/.aicage-custom/base-images/<BASE>/
├─ base.yml (or base.yaml)
└─ Dockerfile
```

## base.yml

```yaml
from_image: debian:bookworm
base_image_distro: Debian
base_image_description: "Debian base image"
architectures:
  - amd64
  - arm64
```

`architectures` is required. Use `amd64` and/or `arm64`.

Only bases matching the current host architecture are offered. For example, an
`amd64`-only base is not shown on `arm64` hosts.

## Dockerfile

The Dockerfile builds the custom base image. The build arg `FROM_IMAGE` is provided:

```Dockerfile
ARG FROM_IMAGE
FROM ${FROM_IMAGE} AS from_image
```

Keep the build non-interactive and deterministic.

## Examples

- [PHP sample](https://github.com/aicage/aicage-custom-samples/tree/main/base-images/php)
- [Debian mirror sample](https://github.com/aicage/aicage-custom-samples/tree/main/base-images/debian-mirror)
