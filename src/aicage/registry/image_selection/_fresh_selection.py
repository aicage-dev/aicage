from aicage.config.context import ConfigContext
from aicage.config.extensions.loader import ExtensionMetadata
from aicage.config.project_config import AgentConfig
from aicage.registry._errors import RegistryError
from aicage.runtime.menu.default_base import resolve_default_base

from ._metadata import available_bases, require_agent_metadata
from .extensions.context import ExtensionSelectionContext
from .extensions.handler import handle_extension_selection
from .interaction import BaseChoiceRequest, SelectionInteraction
from .models import ImageSelection


def fresh_selection(
    agent: str,
    context: ConfigContext,
    extensions: dict[str, ExtensionMetadata],
    selection_interaction: SelectionInteraction,
) -> ImageSelection:
    agent_metadata = require_agent_metadata(agent, context)
    bases = available_bases(agent, context)
    if not bases:
        raise RegistryError(
            f"No base images found for agent '{agent}' in config context."
        )

    base = selection_interaction.choose_base(
        BaseChoiceRequest(
            agent=agent,
            context=context,
            agent_metadata=agent_metadata,
            default_base=resolve_default_base(bases),
        )
    )
    agent_cfg = context.project_cfg.agents.setdefault(agent, AgentConfig())
    agent_cfg.base = base
    return handle_extension_selection(
        ExtensionSelectionContext(
            agent=agent,
            base=base,
            agent_cfg=agent_cfg,
            agent_metadata=agent_metadata,
            extensions=extensions,
            context=context,
        ),
        selection_interaction,
    )
