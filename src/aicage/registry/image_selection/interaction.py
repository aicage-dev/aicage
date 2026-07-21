from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from aicage.config.agent.models import AgentMetadata
from aicage.config.context import ConfigContext


@dataclass(frozen=True)
class BaseChoiceRequest:
    agent: str
    context: ConfigContext
    agent_metadata: AgentMetadata
    default_base: str


@dataclass(frozen=True)
class ExtensionChoiceOption:
    name: str
    description: str


@dataclass(frozen=True)
class MissingExtensionsRequest:
    agent: str
    missing: list[str]
    stored_image_ref: str
    project_config_path: Path
    other_projects: list[tuple[str, Path]]


class SelectionInteraction(Protocol):
    def choose_base(self, request: BaseChoiceRequest) -> str: ...

    def choose_extensions(
        self,
        options: list[ExtensionChoiceOption],
    ) -> list[str]: ...

    def choose_image_ref(self, default_ref: str) -> str: ...

    def choose_missing_extensions(self, request: MissingExtensionsRequest) -> str: ...
