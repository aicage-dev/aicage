# Extensions

Extensions add extra tools on top of an existing agent image. They are defined locally under
`~/.aicage-custom/extensions/` and are applied in the order you select them.

Extensions are the normal answer when software or tools are missing inside the container.

## In the setup screen

After you add an extension under `~/.aicage-custom/extensions/`, rerun `aicage <agent>` and select
it in the `Extensions` view.

![Extensions](screenshots/textual/Screenshot_extensions.png)

The setup screen lists the extensions it finds locally and saves your selection in the project
config when you accept the overview.

## Quick start

```bash
git clone https://github.com/aicage/aicage-custom-samples.git $HOME/.aicage-custom
```

Then rerun `aicage <agent>` and select the extension you want.

## Directory layout

```text
~/.aicage-custom/extensions/<EXTENSION>/
├─ extension.yml (or extension.yaml)
├─ Dockerfile        # optional
└─ scripts/          # optional
   ├─ 01-setup.sh
   └─ 02-install.sh
```

Define at least one of `scripts/` or `shares`.

Only scripts in `scripts/` are executed, in alphabetical order.

## extension.yml

```yaml
name: "Display name"
description: "Short description of what the extension adds."
shares: # optional
  - ~/.config/my-tool
  - ~/.cache/my-tool:ro
```

`shares` can be used to define host mounts. Each entry uses the same syntax as `--share`: `HOST`
or `HOST:ro`.

## Scripts

Scripts run inside the image build. Use `bash`, keep them non-interactive, and fail fast on
errors.

## Dockerfile (optional)

If present, your Dockerfile replaces the built-in extension Dockerfile. The build args provided
are `BASE_IMAGE` and `EXTENSION`.

## Examples

- [Act sample](https://github.com/aicage/aicage-custom-samples/tree/main/extensions/act)
- [Marker sample](https://github.com/aicage/aicage-custom-samples/tree/main/extensions/marker)
