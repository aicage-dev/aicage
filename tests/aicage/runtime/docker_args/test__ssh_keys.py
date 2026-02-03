import tempfile
from pathlib import Path
from unittest import TestCase, mock

from aicage.cli_types import ParsedArgs
from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig, ProjectConfig, _AgentMounts
from aicage.runtime.docker_args import _ssh_keys
from aicage.runtime.docker_args._resolver_types import MountRequest, ResolvedArgs


class SshKeyTests(TestCase):
    def test_resolve_ssh_mount_skips_when_signing_disabled(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts(ssh=True))
        context = _build_context(agent_cfg)
        with mock.patch(
            "aicage.runtime.docker_args._ssh_keys.is_commit_signing_enabled",
            return_value=False,
        ):
            resolved = _ssh_keys.resolve(context, "codex", _build_parsed())
        self.assertEqual(ResolvedArgs(), resolved)

    def test_resolve_ssh_mount_skips_for_non_ssh_format(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts(ssh=True))
        context = _build_context(agent_cfg)
        with (
            mock.patch(
                "aicage.runtime.docker_args._ssh_keys.is_commit_signing_enabled",
                return_value=True,
            ),
            mock.patch(
                "aicage.runtime.docker_args._ssh_keys.resolve_signing_format",
                return_value="gpg",
            ),
        ):
            resolved = _ssh_keys.resolve(context, "codex", _build_parsed())
        self.assertEqual(ResolvedArgs(), resolved)

    def test_resolve_ssh_mount_respects_pref(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts(ssh=False))
        context = _build_context(agent_cfg)
        ssh_dir = Path("/tmp/ssh")
        with (
            mock.patch("aicage.runtime.docker_args._ssh_keys.is_commit_signing_enabled", return_value=True),
            mock.patch("aicage.runtime.docker_args._ssh_keys.resolve_signing_format", return_value="ssh"),
            mock.patch("aicage.runtime.docker_args._ssh_keys.resolve_ssh_dir", return_value=ssh_dir),
        ):
            resolved = _ssh_keys.resolve(context, "codex", _build_parsed())
        self.assertEqual(ResolvedArgs(), resolved)

    def test_resolve_ssh_mount_uses_preference(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts(ssh=True))
        context = _build_context(agent_cfg)
        with tempfile.TemporaryDirectory() as tmp_dir:
            ssh_dir = Path(tmp_dir) / "ssh"
            ssh_dir.mkdir()
            with (
                mock.patch("aicage.runtime.docker_args._ssh_keys.is_commit_signing_enabled", return_value=True),
                mock.patch("aicage.runtime.docker_args._ssh_keys.resolve_signing_format", return_value="ssh"),
                mock.patch("aicage.runtime.docker_args._ssh_keys.resolve_ssh_dir", return_value=ssh_dir),
            ):
                resolved = _ssh_keys.resolve(context, "codex", _build_parsed())
        self.assertEqual(
            ResolvedArgs(mounts=[MountRequest(host_path=ssh_dir)]),
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
