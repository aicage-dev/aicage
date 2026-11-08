"""Credential utility-image preparation."""

from aicage.config.run_config import RunConfig
from aicage.constants import CREDENTIAL_AGENT_IMAGE
from aicage.registry.ensure_util_image import (
    UtilImageSetupAction,
    ensure_util_image,
    util_image_setup_action,
)
from aicage.runtime.menu.interaction import RuntimeInteraction


def prepare_credential_image(
    run_config: RunConfig, interaction: RuntimeInteraction
) -> None:
    agent_cfg = run_config.context.project_cfg.agents.get(run_config.agent)
    if agent_cfg is None or not (agent_cfg.mounts.ssh or agent_cfg.mounts.gnupg):
        return
    setup_action = util_image_setup_action(CREDENTIAL_AGENT_IMAGE)
    if setup_action is UtilImageSetupAction.SKIP:
        return
    interaction.execute_operation(
        lambda reporter: ensure_util_image(
            CREDENTIAL_AGENT_IMAGE,
            reporter,
            setup_action=setup_action,
        )
    )
