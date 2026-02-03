import tempfile
from pathlib import Path
from unittest import TestCase, mock

from aicage.cli_types import ParsedArgs
from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig, ProjectConfig
from aicage.runtime.docker_args import _git_config
from aicage.runtime.docker_args._resolver_types import MountRequest, ResolvedArgs


class GitConfigTests(TestCase):
    def test_resolve_git_config_mount_skips_without_config(self) -> None:
        agent_cfg = AgentConfig()
        context = _build_context(agent_cfg)
        with mock.patch(
            "aicage.runtime.docker_args._git_config.resolve_git_config_path",
            return_value=None,
        ):
            resolved = _git_config.resolve(context, "codex", _build_parsed())
        self.assertEqual(ResolvedArgs(), resolved)

    def test_resolve_git_config_mount_respects_pref(self) -> None:
        agent_cfg = AgentConfig()
        agent_cfg.mounts.gitconfig = True
        context = _build_context(agent_cfg)
        with tempfile.TemporaryDirectory() as tmp_dir:
            gitconfig = Path(tmp_dir) / ".gitconfig"
            gitconfig.write_text("user.name = tester", encoding="utf-8")
            with mock.patch(
                "aicage.runtime.docker_args._git_config.resolve_git_config_path",
                return_value=gitconfig,
            ):
                resolved = _git_config.resolve(context, "codex", _build_parsed())
        self.assertEqual(
            ResolvedArgs(mounts=[MountRequest(host_path=gitconfig)]),
            resolved,
        )


def _build_context(agent_cfg: AgentConfig) -> ConfigContext:
    project_cfg = ProjectConfig(path="/tmp/project", agents={"codex": agent_cfg})
    return ConfigContext(
        store=mock.Mock(),
        project_cfg=project_cfg,
        agents={},
        bases={},
        extensions={},
    )


def _build_parsed() -> ParsedArgs:
    return ParsedArgs(False, "", "codex", [], False, [], None)
