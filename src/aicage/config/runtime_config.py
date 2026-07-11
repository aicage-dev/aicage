from dataclasses import dataclass
from pathlib import Path

from aicage.cli_types import ParsedArgs
from aicage.config.agent.loader import load_agents
from aicage.config.base.loader import load_bases
from aicage.config.config_store import SettingsStore
from aicage.config.context import ConfigContext
from aicage.config.extensions.loader import load_extensions
from aicage.config.run_config_draft import RunConfigDraft, create_run_config_draft
from aicage.registry.image_selection.models import ImageSelection
from aicage.registry.image_selection.selection import select_agent_image
from aicage.runtime.docker_args.mount_preferences import apply_mount_preferences
from aicage.runtime.docker_args.resolve.resolver import resolve_docker_args
from aicage.runtime.prompts.confirm import prompt_persist_docker_args, prompt_persist_shares
from aicage.runtime.run_args import EnvVar, MountSpec


@dataclass(frozen=True)
class RunConfig:
    project_path: Path
    agent: str
    context: ConfigContext
    selection: ImageSelection
    project_docker_args: str
    mounts: list[MountSpec]
    env: list[EnvVar]


def load_run_config(agent: str, parsed: ParsedArgs | None = None) -> RunConfig:
    store = SettingsStore()
    project_path = Path.cwd().resolve()
    bases = load_bases()
    agents = load_agents(bases)
    draft = create_run_config_draft(project_path, agent, store.load_project(project_path), parsed)
    context = ConfigContext(
        store=store,
        project_cfg=draft.project_cfg,
        agents=agents,
        bases=bases,
        extensions=load_extensions(),
    )
    selection = select_agent_image(agent, context)
    draft.apply_selection(selection)
    _persist_docker_args(draft)
    _persist_shares(draft)
    apply_mount_preferences(context, agent, parsed)
    project_docker_args = draft.existing_project_docker_args
    mounts, env = resolve_docker_args(context, agent, parsed)
    store.save_project(project_path, draft.project_cfg)

    return RunConfig(
        project_path=project_path,
        agent=agent,
        context=context,
        selection=selection,
        project_docker_args=project_docker_args,
        mounts=mounts,
        env=env,
    )


def _persist_docker_args(draft: RunConfigDraft) -> None:
    if draft.parsed is None or not draft.parsed.docker_args:
        return
    existing = draft.agent_cfg.docker_args
    if existing == draft.parsed.docker_args:
        return
    draft.persist_docker_args(
        prompt_persist_docker_args(draft.parsed.docker_args, existing),
    )


def _persist_shares(draft: RunConfigDraft) -> None:
    if draft.parsed is None:
        return
    existing_shares = list(draft.agent_cfg.shares)
    new_shares = draft.persist_shares(False)
    if not new_shares:
        return
    draft.persist_shares(prompt_persist_shares(new_shares, existing_shares))
