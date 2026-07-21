from aicage.config.extended_images import (
    ExtendedImageConfig,
    extended_image_config_path,
    write_extended_image_config,
)
from aicage.config.image_refs import default_extended_image_ref

from ..interaction import ExtensionChoiceOption, SelectionInteraction
from ..models import ImageSelection
from .context import ExtensionSelectionContext
from .refs import base_image_ref


def handle_extension_selection(
    selection: ExtensionSelectionContext,
    selection_interaction: SelectionInteraction,
) -> ImageSelection:
    agent_cfg = selection.agent_cfg
    agent_cfg.base = selection.base
    extension_options = [
        ExtensionChoiceOption(
            name=ext.extension_id,
            description=f"{ext.name}: {ext.description}",
        )
        for ext in sorted(
            selection.extensions.values(), key=lambda item: item.extension_id
        )
    ]
    selected_extensions = (
        selection_interaction.choose_extensions(extension_options)
        if extension_options
        else []
    )
    if selected_extensions:
        image_ref = selection_interaction.choose_image_ref(
            _default_extended_image_ref(
                selection.agent, selection.base, selected_extensions
            )
        )
        agent_cfg.extensions = list(selected_extensions)
        agent_cfg.image_ref = image_ref
        write_extended_image_config(
            ExtendedImageConfig(
                name=_extended_image_name(image_ref),
                agent=selection.agent,
                base=selection.base,
                extensions=list(selected_extensions),
                image_ref=image_ref,
                path=extended_image_config_path(_extended_image_name(image_ref)),
            )
        )
    else:
        agent_cfg.extensions = []
        agent_cfg.image_ref = base_image_ref(
            selection.agent_metadata,
            selection.agent,
            selection.base,
            selection.context,
        )
    return ImageSelection(
        image_ref=agent_cfg.image_ref or "",
        base=selection.base,
        extensions=list(agent_cfg.extensions),
        base_image_ref=base_image_ref(
            selection.agent_metadata,
            selection.agent,
            selection.base,
            selection.context,
        ),
    )


def _default_extended_image_ref(agent: str, base: str, extensions: list[str]) -> str:
    return default_extended_image_ref(agent, base, extensions)


def _extended_image_name(image_ref: str) -> str:
    _, _, tag = image_ref.rpartition(":")
    return tag or image_ref
