# Images and layers

`aicage` uses a three-layer image model.

## 1) Base image

The base image is the OS + shared dev tooling. It is the foundation for all agents.

For a detailed list of installed tooling, see [Base image tooling](Base-Image-Tooling).

## 2) Agent image

An agent image is a base image plus a specific coding agent. This is what you run with
`aicage <agent>`.

Some built-in agents cannot be redistributed due to licensing. For those agents, `aicage` builds
the image locally on your machine when needed.

## 3) Extensions (optional)

Extensions let you add extra tooling on top of an existing agent image. Extensions are always
local and are applied in the order you select them.

## Built-in vs custom

Each layer can come from:

- Built-in definitions provided by `aicage`.
- Custom definitions you place under `~/.aicage-custom`.

If a custom definition uses the same name as a built-in one, the custom entry overrides it.
