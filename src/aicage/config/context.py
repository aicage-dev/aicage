from dataclasses import dataclass

from aicage.config.agent.models import AgentMetadata
from aicage.config.base.models import BaseMetadata
from aicage.config.extensions.loader import ExtensionMetadata
from aicage.constants import IMAGE_REGISTRY, IMAGE_REPOSITORY

from .config_store import SettingsStore
from .project_config import _ProjectConfig


@dataclass
class ConfigContext:
    store: SettingsStore
    project_cfg: _ProjectConfig
    agents: dict[str, AgentMetadata]
    bases: dict[str, BaseMetadata]
    extensions: dict[str, ExtensionMetadata]

    @staticmethod
    def image_repository_ref() -> str:
        return f"{IMAGE_REGISTRY}/{IMAGE_REPOSITORY}"
