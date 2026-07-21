from dataclasses import dataclass

from aicage.config.run_config import RunConfig
from aicage.docker.reporting import OperationReporter
from aicage.paths import CUSTOM_BASES_DIR
from aicage.registry._image_pull import pull_image
from aicage.registry._pull_decision import pull_decision_plan
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
    needs_update_confirmation: bool = False


def ensure_image(
    run_config: RunConfig,
    update_approved: bool,
    reporter: OperationReporter | None = None,
) -> None:
    agent_metadata = run_config.context.agents[run_config.agent]
    base_metadata = run_config.context.bases[run_config.selection.base]
    custom_base = base_metadata.local_definition_dir.is_relative_to(CUSTOM_BASES_DIR)
    if not agent_metadata.build_local and not custom_base:
        pull_image(
            run_config.selection.base_image_ref,
            update_approved=update_approved,
            reporter=reporter,
        )
    else:
        ensure_agent_image(
            run_config,
            update_approved=update_approved,
            reporter=reporter,
        )
    if run_config.selection.extensions:
        ensure_extended_image(run_config, reporter=reporter)


def image_setup_plan(run_config: RunConfig) -> ImageSetupPlan:
    agent_metadata = run_config.context.agents[run_config.agent]
    base_metadata = run_config.context.bases[run_config.selection.base]
    custom_base = base_metadata.local_definition_dir.is_relative_to(CUSTOM_BASES_DIR)
    needs_update_confirmation = False
    needs_setup = False
    if not agent_metadata.build_local and not custom_base:
        pull_plan = pull_decision_plan(run_config.selection.base_image_ref)
        needs_setup = pull_plan.should_pull
        needs_update_confirmation = pull_plan.needs_confirmation
    elif agent_metadata.build_local or custom_base:
        agent_plan = agent_build_setup_plan(run_config)
        needs_setup = agent_plan.needs_setup
        needs_update_confirmation = agent_plan.needs_update_confirmation
    if run_config.selection.extensions and extension_build_needed(run_config):
        needs_setup = True
    return ImageSetupPlan(
        needs_setup=needs_setup or needs_update_confirmation,
        needs_update_confirmation=needs_update_confirmation,
    )
