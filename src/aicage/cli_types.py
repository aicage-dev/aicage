from dataclasses import dataclass
from typing import Literal

_MenuMode = Literal["textual", "simple", "none"]


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
    menu: _MenuMode = "textual"
