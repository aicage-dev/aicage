from collections.abc import Callable

from aicage.config.run_config import RunConfig
from aicage.registry.ensure_image import (
    ImageSetupPlan,
    ensure_image,
    image_setup_needed,
    image_setup_plan,
)
from aicage.runtime.menu.interaction import RuntimeInteraction

_ConfirmImageUpdate = Callable[[str], bool]


def prepare_image(run_config: RunConfig, interaction: RuntimeInteraction) -> None:
    setup_plan = image_setup_plan(run_config)
    confirm_update = _confirm_update(setup_plan, interaction)
    if not image_setup_needed(run_config, confirm_update):
        return
    interaction.execute_image_setup(
        lambda reporter: ensure_image(
            run_config,
            reporter=reporter,
            confirm_update=confirm_update,
        )
    )


def _confirm_update(
    setup_plan: ImageSetupPlan,
    interaction: RuntimeInteraction,
) -> _ConfirmImageUpdate:
    image_ref = setup_plan.confirm_update_image_ref
    if image_ref is None:
        return _keep_local_image
    should_update = interaction.confirm_image_update(image_ref)
    return _confirm_image_update_choice(image_ref, should_update)


def _keep_local_image(_: str) -> bool:
    return False


def _confirm_image_update_choice(
    image_ref: str,
    should_update: bool,
) -> _ConfirmImageUpdate:
    def _confirm(candidate_image_ref: str) -> bool:
        if candidate_image_ref != image_ref:
            raise RuntimeError(
                f"Unexpected image update request for '{candidate_image_ref}'."
            )
        return should_update

    return _confirm
