from typing import Protocol

from aicage.cli_types import MenuMode
from aicage.config.context import ConfigContext
from aicage.config.run_config_draft import RunConfigDraft
from aicage.runtime.menu._interaction_types import (
    ConfigSelectionResult,
    ImageSetupOperation,
)
from aicage.runtime.menu._none_interaction import create_none_interaction
from aicage.runtime.menu.prompts.interaction import SimpleInteraction
from aicage.runtime.menu.textual.interaction import TextualInteraction


class RuntimeInteraction(Protocol):
    def configure_run(
        self,
        draft: RunConfigDraft,
        context: ConfigContext,
        agent: str,
    ) -> ConfigSelectionResult: ...

    def confirm_aicage_update(
        self,
        installed_version: str,
        latest_version: str,
    ) -> bool: ...

    def confirm_image_update(self, image_ref: str) -> bool: ...

    def execute_image_setup(self, operation: ImageSetupOperation) -> None: ...


def create_runtime_interaction(menu: MenuMode) -> RuntimeInteraction:
    if menu == "ui":
        return TextualInteraction()
    if menu == "none":
        return create_none_interaction()
    return SimpleInteraction()
