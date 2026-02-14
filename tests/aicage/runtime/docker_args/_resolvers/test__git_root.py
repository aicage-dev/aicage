from pathlib import Path
from unittest import TestCase, mock

from aicage.config.project_config import AgentConfig, _AgentMounts
from aicage.runtime.docker_args._resolvers import _git_root
from aicage.runtime.docker_args._support._resolver_types import MountRequest, ResolvedArgs

from ._fixtures import build_context, build_parsed

_MODULE = "aicage.runtime.docker_args._resolvers._git_root"


class GitRootTests(TestCase):
    def test_resolve_git_root_mount_skips_without_git_root(self) -> None:
        agent_cfg = AgentConfig()
        context = build_context(agent_cfg)
        with (
            mock.patch(f"{_MODULE}.resolve_git_root", return_value=None),
        ):
            resolved = _git_root.resolve(context, "codex", build_parsed())
        self.assertEqual(ResolvedArgs(), resolved)

    def test_resolve_git_root_mount_skips_for_project_root(self) -> None:
        agent_cfg = AgentConfig()
        context = build_context(agent_cfg)
        with (
            mock.patch(f"{_MODULE}.resolve_git_root", return_value=Path("/tmp/project")),
        ):
            resolved = _git_root.resolve(context, "codex", build_parsed())
        self.assertEqual(ResolvedArgs(), resolved)

    def test_resolve_git_root_mount_respects_pref(self) -> None:
        git_root = Path("/tmp/root")
        agent_cfg = AgentConfig(mounts=_AgentMounts(gitroot=False))
        context = build_context(agent_cfg)
        with mock.patch(
            f"{_MODULE}.resolve_git_root",
            return_value=git_root,
        ):
            resolved = _git_root.resolve(context, "codex", build_parsed())
        self.assertEqual(ResolvedArgs(), resolved)

    def test_resolve_git_root_mount_uses_preference(self) -> None:
        git_root = Path("/tmp/root")
        agent_cfg = AgentConfig(mounts=_AgentMounts(gitroot=True))
        context = build_context(agent_cfg)
        with mock.patch(
            f"{_MODULE}.resolve_git_root",
            return_value=git_root,
        ):
            resolved = _git_root.resolve(context, "codex", build_parsed())
        self.assertEqual(
            ResolvedArgs(mounts=[MountRequest(host_path=git_root)]),
            resolved,
        )
