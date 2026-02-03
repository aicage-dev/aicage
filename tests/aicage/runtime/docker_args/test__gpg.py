import tempfile
from pathlib import Path
from unittest import TestCase, mock

from aicage.cli_types import ParsedArgs
from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig, ProjectConfig, _AgentMounts
from aicage.runtime.docker_args import _gpg
from aicage.runtime.docker_args._resolver_types import MountRequest, ResolvedArgs


class GpgHomeTests(TestCase):
    def test_resolve_gpg_mount_skips_when_signing_disabled(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts(gnupg=True))
        context = _build_context(agent_cfg)
        with mock.patch(
            "aicage.runtime.docker_args._gpg.is_commit_signing_enabled",
            return_value=False,
        ):
            resolved = _gpg.resolve(context, "codex", _build_parsed())
        self.assertEqual(ResolvedArgs(), resolved)

    def test_resolve_gpg_mount_skips_for_ssh_format(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts(gnupg=True))
        context = _build_context(agent_cfg)
        with (
            mock.patch(
                "aicage.runtime.docker_args._gpg.is_commit_signing_enabled",
                return_value=True,
            ),
            mock.patch(
                "aicage.runtime.docker_args._gpg.resolve_signing_format",
                return_value="ssh",
            ),
        ):
            resolved = _gpg.resolve(context, "codex", _build_parsed())
        self.assertEqual(ResolvedArgs(), resolved)

    def test_resolve_gpg_mount_respects_pref(self) -> None:
        gpg_home = Path("/tmp/gpg")
        agent_cfg = AgentConfig(mounts=_AgentMounts(gnupg=False))
        context = _build_context(agent_cfg)
        with (
            mock.patch(
                "aicage.runtime.docker_args._gpg.is_commit_signing_enabled",
                return_value=True,
            ),
            mock.patch(
                "aicage.runtime.docker_args._gpg.resolve_signing_format",
                return_value="gpg",
            ),
            mock.patch(
                "aicage.runtime.docker_args._gpg.resolve_gpg_home",
                return_value=gpg_home,
            ),
        ):
            resolved = _gpg.resolve(context, "codex", _build_parsed())
        self.assertEqual(ResolvedArgs(), resolved)

    def test_resolve_gpg_mount_uses_preference(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts(gnupg=True))
        context = _build_context(agent_cfg)
        with tempfile.TemporaryDirectory() as tmp_dir:
            gpg_home = Path(tmp_dir) / "gnupg"
            gpg_home.mkdir()
            with (
                mock.patch(
                    "aicage.runtime.docker_args._gpg.is_commit_signing_enabled",
                    return_value=True,
                ),
                mock.patch(
                    "aicage.runtime.docker_args._gpg.resolve_signing_format",
                    return_value="gpg",
                ),
                mock.patch(
                    "aicage.runtime.docker_args._gpg.resolve_gpg_home",
                    return_value=gpg_home,
                ),
            ):
                resolved = _gpg.resolve(context, "codex", _build_parsed())
        self.assertEqual(
            ResolvedArgs(mounts=[MountRequest(host_path=gpg_home)]),
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
