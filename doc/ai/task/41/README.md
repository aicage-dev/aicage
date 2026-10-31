# Task 41: Add acp-wsl to aicage

IDE plugins on Windows send Windows paths in the ACP protocol.
Agents running in Linux Docker containers on WSL do not understand those paths.

And with [aicage/acp-wsl](https://github.com/aicage/acp-wsl) (fork
[aicage-dev/acp-wsl](https://github.com/aicage-dev/acp-wsl), local in [acp-wsl](../../../../../acp-wsl)) I now have a
working _ACP proxy for Windows ↔ WSL path translation_.

- [aicage issue 124](https://github.com/aicage/aicage/issues/124) about the ACP path problem
- [release in fork](https://github.com/aicage-dev/acp-wsl/releases/tag/v1.0.0-alpha02), `aicage/acp-wsl` has no releases
  yet

## Existing PoC as extension

Look at:

- aicage-custom-samples/extensions/acp-wsl/scripts/01-acp-wsl.sh
- aicage.wiki/Customization-Extensions.md

Currently `acp-wsl` is just a PoC extension. But it works fine so far, I just have to pass
`-e AICAGE_ENTRYPOINT_CMD=acp-wsl-agent` as docker-run argument. Good enough for the PoC.

Now I want to integrate this into `aicage` in a user-friendly manner.

## Task Steps

These are my ideas. Feel free to suggest alternatives.

## 1. Install `acp-wsl` in the base images

I'm thinking of adding a new script to
[aicage-image-base/scripts/os-installers/generic](../../../../../aicage-image-base/scripts/os-installers/generic).

And starting calling that from a new script in each `aicage-image-base/scripts/os-installers/distro/*/install` folder.

For now, it would use the binaries from the `latest` release of my fork
[aicage-dev/acp-wsl](https://github.com/aicage-dev/acp-wsl).

Add a simple test script in [aicage-image-base/tests/bases/smoke/default](../../../../../aicage-image-base/tests/bases/smoke/default).

In all 3 cases look at existing scripts in target folders and follow the same patterns.

## 2. Trigger use in image entrypoint

The image entrypoint script is in [entrypoint.sh](../../../../../aicage-image-base/scripts/entrypoint.sh).

`entrypoint.sh` already reacts to quite a few situations. For `acp-wsl` my current idea is that the entrypoint activates
use of `acp-wsl` when a new Aicage environment variable is present.

Add a new `aicage-image-base/tests/bases/smoke/default/9x-entrypoint-<purpose>.bats` to test the new behavior of the
entrypoint.

Update the docs in [Entrypoint contract](../../../../../aicage.wiki/Entrypoint-Contract.md)

Again, follow existing patterns.

## 3. Add new CLI argument `--acp-wsl` to Aicage

The Python `aicage` in repo [aicage/aicage](../../../..) should get a new CLI argument `--acp-wsl` which can be no more than
a shortcut to set the env-var the `entrypoint.sh` reacts to.

For this make sure to read and respect guidelines and rules in:

- [aicage/AGENTS.md](../../../../AGENTS.md)
- [aicage/doc/python-test-structure-guidelines.md](../../../python-test-structure-guidelines.md)

Also update the [CLI options](../../../../../aicage.wiki/CLI-Options.md) docs.

## 4. Extra ACP scripts by Aicage for agents needing external ACP bridge

See [ACP Bridge for Amp, Claude, and Codex](../../../../README.md#acp-bridge-for-amp-claude-and-codex).

[pyproject.toml](../../../../pyproject.toml) has 3 extra scripts next to `aicage`.

```toml
[project.scripts]
aicage = "aicage.cli.entrypoint:main"
aicage-amp = "aicage.cli.agent_entrypoints:amp"
aicage-claude = "aicage.cli.agent_entrypoints:claude"
aicage-codex = "aicage.cli.agent_entrypoints:codex"
```

The only reason to have them is that the external bridges all expect a single command without args in their env-var
`CODEX_PATH` resp. `CLAUDE_CODE_EXECUTABLE`. See [acp.json](../../../../config/ide-plugins/JetBrains/acp.json) for examples.

I'm not yet totally sure but think as extra Aicage scripts serve for ACP communication only, they should auto-set the
new `--acp-wsl` and maybe check that it's not already in the args to aicage.

## 5. Update documentation

I'm not sure if this is interesting enough to users to have a full page about it in the
[aicage.wiki](../../../../../aicage.wiki).

But it should be documented somehow with reference to the [aicage/acp-wsl](https://github.com/aicage/acp-wsl) repo. That
repo is the better place for a thorough documentation. I would not over-explain this in docs for Aicage.

Also, the user-facing docs for ACP config and config examples on Windows should be updated. The config examples should
already show the new `--acp-wsl` parameter for Windows.
