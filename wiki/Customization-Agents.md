# Custom agents

Custom agents are local agent installs that build into local Docker images. They live under
`~/.aicage-custom/agents/` and behave like locally built built-in agents.

If a custom agent name matches a built-in agent name, the custom agent overrides it.

## Directory layout

```text
~/.aicage-custom/agents/<AGENT>/
├─ agent.yaml (or agent.yml)
├─ install.sh
└─ version.sh
```

The directory name is the agent id used on the CLI, for example: `aicage <AGENT>`.

## agent.yaml

Required keys:

```yaml
agent_full_name: Forge Code
agent_homepage: https://forgecode.dev/
```

Optional keys:

```yaml
agent_path:
  directories:
    - ~/.forge
  files:
    - ~/sample.txt
base_exclude:
  - alpine
base_distro_exclude:
  - debian
```

Notes:

- `agent_path.directories` lists directory paths to mount.
- `agent_path.files` lists file paths to mount.
- `base_exclude` removes specific base ids from the selection list for this agent.
- `base_distro_exclude` removes bases by distro name (from the base metadata).

## install.sh

Runs during the Docker build of the local image. Keep it deterministic and non-interactive.

## version.sh

Outputs the agent version string that drives rebuild decisions.

## Example

Sample custom agent files:

- [Forge sample](https://github.com/aicage/aicage-custom-samples/tree/main/agents/forge)
