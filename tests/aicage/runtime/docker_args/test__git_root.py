from pathlib import Path
from unittest import TestCase, mock

from aicage.cli_types import ParsedArgs
from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig, ProjectConfig, _AgentMounts
from aicage.runtime.docker_args import _git_root
from aicage.runtime.docker_args._resolver_types import MountRequest, ResolvedArgs


class GitRootTests(TestCase):
    def test_resolve_git_root_mount_skips_without_git_root(self) -> None:
        agent_cfg = AgentConfig()
        context = _build_context(agent_cfg)
        with (
            mock.patch("aicage.runtime.docker_args._git_root.resolve_git_root", return_value=None),
        ):
            resolved = _git_root.resolve(context, "codex", _build_parsed())
        self.assertEqual(ResolvedArgs(), resolved)

    def test_resolve_git_root_mount_skips_for_project_root(self) -> None:
        agent_cfg = AgentConfig()
        context = _build_context(agent_cfg)
        with (
            mock.patch("aicage.runtime.docker_args._git_root.resolve_git_root", return_value=Path("/tmp/project")),
        ):
            resolved = _git_root.resolve(context, "codex", _build_parsed())
        self.assertEqual(ResolvedArgs(), resolved)

    def test_resolve_git_root_mount_respects_pref(self) -> None:
        git_root = Path("/tmp/root")
        agent_cfg = AgentConfig(mounts=_AgentMounts(gitroot=False))
        context = _build_context(agent_cfg)
        with mock.patch(
            "aicage.runtime.docker_args._git_root.resolve_git_root",
            return_value=git_root,
        ):
            resolved = _git_root.resolve(context, "codex", _build_parsed())
        self.assertEqual(ResolvedArgs(), resolved)

    def test_resolve_git_root_mount_uses_preference(self) -> None:
        git_root = Path("/tmp/root")
        agent_cfg = AgentConfig(mounts=_AgentMounts(gitroot=True))
        context = _build_context(agent_cfg)
        with mock.patch(
            "aicage.runtime.docker_args._git_root.resolve_git_root",
            return_value=git_root,
        ):
            resolved = _git_root.resolve(context, "codex", _build_parsed())
        self.assertEqual(
            ResolvedArgs(mounts=[MountRequest(host_path=git_root)]),
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
