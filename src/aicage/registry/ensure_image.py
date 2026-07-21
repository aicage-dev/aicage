from dataclasses import dataclass

from aicage.config.run_config import RunConfig
from aicage.docker.reporting import OperationReporter
from aicage.paths import CUSTOM_BASES_DIR
from aicage.registry._image_pull import pull_image
from aicage.registry._pull_decision import (
    ConfirmImageUpdate,
    decide_pull,
    pull_decision_plan,
)
from aicage.registry.agent_build.ensure import (
    build_needed as agent_build_needed,
)
from aicage.registry.agent_build.ensure import (
    ensure as ensure_agent_image,
)
from aicage.registry.agent_build.ensure import (
    setup_plan as agent_build_setup_plan,
)
from aicage.registry.extension_build.ensure import (
    build_needed as extension_build_needed,
)
from aicage.registry.extension_build.ensure import ensure as ensure_extended_image


@dataclass(frozen=True)
class ImageSetupPlan:
    needs_setup: bool
    confirm_update_image_ref: str | None = None


def _confirm_update_pull(_: str) -> bool:
    return True


def ensure_image(
    run_config: RunConfig,
    reporter: OperationReporter | None = None,
    confirm_update: ConfirmImageUpdate | None = None,
) -> None:
    resolved_confirm_update = confirm_update or _confirm_update_pull
    agent_metadata = run_config.context.agents[run_config.agent]
    base_metadata = run_config.context.bases[run_config.selection.base]
    custom_base = base_metadata.local_definition_dir.is_relative_to(CUSTOM_BASES_DIR)
    if not agent_metadata.build_local and not custom_base:
        pull_image(
            run_config.selection.base_image_ref,
            reporter=reporter,
            confirm_update=resolved_confirm_update,
        )
    else:
        ensure_agent_image(
            run_config,
            reporter=reporter,
            confirm_update=resolved_confirm_update,
        )
    if run_config.selection.extensions:
        ensure_extended_image(run_config, reporter=reporter)


def image_setup_plan(run_config: RunConfig) -> ImageSetupPlan:
    agent_metadata = run_config.context.agents[run_config.agent]
    base_metadata = run_config.context.bases[run_config.selection.base]
    custom_base = base_metadata.local_definition_dir.is_relative_to(CUSTOM_BASES_DIR)
    confirm_update_image_ref: str | None = None
    needs_setup = False
    if not agent_metadata.build_local and not custom_base:
        pull_plan = pull_decision_plan(run_config.selection.base_image_ref)
        needs_setup = pull_plan.should_pull
        confirm_update_image_ref = pull_plan.confirm_update_image_ref
    elif agent_metadata.build_local or custom_base:
        agent_plan = agent_build_setup_plan(run_config)
        needs_setup = agent_plan.needs_setup
        confirm_update_image_ref = agent_plan.confirm_update_image_ref
    if run_config.selection.extensions and extension_build_needed(run_config):
        needs_setup = True
    return ImageSetupPlan(
        needs_setup=needs_setup or confirm_update_image_ref is not None,
        confirm_update_image_ref=confirm_update_image_ref,
    )


def image_setup_needed(
    run_config: RunConfig,
    confirm_update: ConfirmImageUpdate | None = None,
) -> bool:
    resolved_confirm_update = confirm_update or _confirm_update_pull
    agent_metadata = run_config.context.agents[run_config.agent]
    base_metadata = run_config.context.bases[run_config.selection.base]
    custom_base = base_metadata.local_definition_dir.is_relative_to(CUSTOM_BASES_DIR)
    if not agent_metadata.build_local and not custom_base:
        pull_needed = decide_pull(
            run_config.selection.base_image_ref,
            resolved_confirm_update,
        )
    else:
        if confirm_update is None:
            return True
        pull_needed = agent_build_needed(run_config, confirm_update)
    if pull_needed:
        return True
    if not run_config.selection.extensions:
        return False
    return extension_build_needed(run_config)
