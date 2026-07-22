from aicage.config.run_config import RunConfig
from aicage.registry.ensure_image import (
    ImageSetupPlan,
    ensure_image,
    image_setup_plan,
)
from aicage.runtime.menu.interaction import RuntimeInteraction


def prepare_image(run_config: RunConfig, interaction: RuntimeInteraction) -> None:
    setup_plan = image_setup_plan(run_config)
    if not setup_plan.needs_setup and not setup_plan.needs_update_confirmation:
        return
    update_approved = _resolve_update_approval(run_config, setup_plan, interaction)
    if not setup_plan.needs_setup and not update_approved:
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
    if not setup_plan.needs_update_confirmation:
        return False
    return interaction.confirm_image_update(run_config.selection.base_image_ref)
