from dataclasses import dataclass, field
from typing import Literal

MenuMode = Literal["ui", "none"]


@dataclass
class ParsedArgs:
    dry_run: bool
    docker_args: str
    agent: str
    agent_args: list[str]
    docker_socket: bool
    shares: list[str]
    config_action: str | None
    config_agent: str | None = None
    menu: MenuMode = "ui"
    extensions: list[str] = field(default_factory=list)
    config_scope: str | None = None
    git: bool | None = None
    base: str | None = None
