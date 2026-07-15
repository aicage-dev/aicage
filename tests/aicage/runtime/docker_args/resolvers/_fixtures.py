from unittest import mock

from aicage.cli_types import ParsedArgs
from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig, ProjectConfig


def build_context(agent_cfg: AgentConfig) -> ConfigContext:
    project_cfg = ProjectConfig(path="/test-tmp/project", agents={"codex": agent_cfg})
    return ConfigContext(
        store=mock.Mock(),
        project_cfg=project_cfg,
        agents={},
        bases={},
        extensions={},
    )


def build_parsed() -> ParsedArgs:
    return ParsedArgs(False, "", "codex", [], False, [], None)
