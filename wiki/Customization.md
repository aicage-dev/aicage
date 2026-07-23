# Customization

`aicage` lets you customize images at three levels: extensions, agents, and base images. The
sample repo is a fast way to see working examples and copy a template.

## Quick start

```bash
git clone https://github.com/aicage/aicage-custom-samples.git $HOME/.aicage-custom
```

Then run any agent (replace `<agent>` with your agent):

```bash
aicage <agent>
```

These are only samples. Use them to learn the structure, then replace or edit them with your own
definitions. `aicage` detects whatever you place under `~/.aicage-custom` and offers it during
selection.

After adding or changing custom definitions, restart `aicage`.

## Choose a path

- [Extensions](Customization-Extensions) when software or tools are missing inside the container
- [Extensions](Customization-Extensions)
- [Custom agents](Customization-Agents)
- [Custom base images](Customization-Base-Images)
