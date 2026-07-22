from pathlib import Path

from aicage.cli_types import ParsedArgs
from aicage.config.agent.loader import load_agents
from aicage.config.agent.models import AgentMetadata
from aicage.config.base.loader import load_bases
from aicage.config.config_store import SettingsStore
from aicage.config.context import ConfigContext
from aicage.config.extensions.loader import load_extensions
from aicage.config.run_config import RunConfig
from aicage.config.run_config_draft import _create_run_config_draft
from aicage.registry.errors import RegistryError
from aicage.runtime.docker_args.resolve.resolver import resolve_docker_args
from aicage.runtime.menu.interaction import RuntimeInteraction


def load_run_config(
    agent: str,
    interaction: RuntimeInteraction,
    parsed: ParsedArgs | None = None,
) -> RunConfig:
    store = SettingsStore()
    project_path = Path.cwd().resolve()
    bases = load_bases()
    agents = load_agents(bases)
    _require_known_agent(agent, agents)
    draft = _create_run_config_draft(
        project_path, agent, store.load_project(project_path), parsed
    )
    context = ConfigContext(
        store=store,
        project_cfg=draft.project_cfg,
        agents=agents,
        bases=bases,
        extensions=load_extensions(),
    )
    result = interaction.configure_run(draft, context, agent)
    mounts, env = resolve_docker_args(context, agent, parsed)
    store.save_project(project_path, draft.project_cfg)

    return RunConfig(
        project_path=project_path,
        agent=agent,
        context=context,
        selection=result.selection,
        project_docker_args=result.project_docker_args,
        mounts=mounts,
        env=env,
    )


def _require_known_agent(agent: str, agents: dict[str, AgentMetadata]) -> None:
    if agent in agents:
        return
    if agent == "config":
        raise RegistryError(
            _unknown_agent_message(
                "Unknown agent 'config'. Use '--config' for config commands.",
                agents,
            )
        )
    raise RegistryError(_unknown_agent_message(f"Unknown agent '{agent}'.", agents))


def _unknown_agent_message(
    message: str,
    agents: dict[str, AgentMetadata],
) -> str:
    if not agents:
        return message
    agent_list = ", ".join(sorted(agents))
    return f"{message} Available agents: {agent_list}."
