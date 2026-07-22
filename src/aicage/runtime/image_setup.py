from aicage.config.run_config import RunConfig
from aicage.registry.ensure_image import (
    ImageSetupAction,
    ImageSetupPlan,
    ensure_image,
    image_setup_plan,
)
from aicage.runtime.menu.interaction import RuntimeInteraction


def prepare_image(run_config: RunConfig, interaction: RuntimeInteraction) -> None:
    setup_plan = image_setup_plan(run_config)
    if setup_plan.action is ImageSetupAction.SKIP:
        return
    update_approved = _resolve_update_approval(run_config, setup_plan, interaction)
    if setup_plan.action is ImageSetupAction.CONFIRM_UPDATE and not update_approved:
        return
    interaction.execute_image_setup(
        lambda reporter: ensure_image(
            run_config,
            update_approved=update_approved,
            reporter=reporter,
        )
    )


def _resolve_update_approval(
    run_config: RunConfig,
    setup_plan: ImageSetupPlan,
    interaction: RuntimeInteraction,
) -> bool:
    if setup_plan.action not in (
        ImageSetupAction.CONFIRM_UPDATE,
        ImageSetupAction.CONFIRM_UPDATE_AND_DO_SETUP,
    ):
        return False
    return interaction.confirm_image_update(run_config.selection.base_image_ref)
