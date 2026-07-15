from aicage.config.run_config import RunConfig
from aicage.docker.reporting import OperationReporter
from aicage.paths import CUSTOM_BASES_DIR
from aicage.registry._image_pull import pull_image
from aicage.registry._pull_decision import decide_pull
from aicage.registry.agent_build.ensure import build_needed as agent_build_needed
from aicage.registry.agent_build.ensure import ensure as ensure_agent_image
from aicage.registry.extension_build.ensure import (
    build_needed as extension_build_needed,
)
from aicage.registry.extension_build.ensure import ensure as ensure_extended_image


def ensure_image(
    run_config: RunConfig, reporter: OperationReporter | None = None
) -> None:
    agent_metadata = run_config.context.agents[run_config.agent]
    base_metadata = run_config.context.bases[run_config.selection.base]
    custom_base = base_metadata.local_definition_dir.is_relative_to(CUSTOM_BASES_DIR)
    if not agent_metadata.build_local and not custom_base:
        pull_image(run_config.selection.base_image_ref, reporter=reporter)
    else:
        ensure_agent_image(run_config, reporter=reporter)
    if run_config.selection.extensions:
        ensure_extended_image(run_config, reporter=reporter)


def image_setup_needed(run_config: RunConfig) -> bool:
    agent_metadata = run_config.context.agents[run_config.agent]
    base_metadata = run_config.context.bases[run_config.selection.base]
    custom_base = base_metadata.local_definition_dir.is_relative_to(CUSTOM_BASES_DIR)
    if not agent_metadata.build_local and not custom_base:
        if decide_pull(run_config.selection.base_image_ref):
            return True
    elif agent_build_needed(run_config):
        return True
    if not run_config.selection.extensions:
        return False
    return extension_build_needed(run_config)
