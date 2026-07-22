from unittest import TestCase, mock

from aicage.cli_types import ParsedArgs
from aicage.config.context import ConfigContext
from aicage.config.project_config import (
    MOUNT_GITCONFIG_KEY,
    MOUNT_GNUPG_KEY,
    AgentConfig,
    _AgentMounts,
    _ProjectConfig,
)
from aicage.runtime.docker_args.mount_preferences import apply_mount_preferences

_MODULE = "aicage.runtime.docker_args.mount_preferences"


class MountPreferencesTests(TestCase):
    def test_apply_mount_preferences_persists_git_mount_choices(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts())
        context = _build_context(agent_cfg)

        with mock.patch(
            f"{_MODULE}.resolve_mount_prompt_prefs",
            return_value=mock.Mock(
                git_mounts={MOUNT_GITCONFIG_KEY, MOUNT_GNUPG_KEY},
                extension_mounts={"marker": True},
            ),
        ):
            apply_mount_preferences(
                context,
                "codex",
                _build_parsed(),
                mock.Mock(),
                mock.Mock(),
            )

        self.assertTrue(agent_cfg.mounts.gitconfig)
        self.assertFalse(agent_cfg.mounts.gitroot)
        self.assertTrue(agent_cfg.mounts.gnupg)
        self.assertFalse(agent_cfg.mounts.ssh)
        self.assertEqual({"marker": True}, agent_cfg.extension_mounts)

    def test_apply_mount_preferences_persists_docker_socket_preference(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts())
        context = _build_context(agent_cfg)

        confirm_persist = mock.Mock(return_value=True)

        with mock.patch(f"{_MODULE}.resolve_mount_prompt_prefs", return_value=None):
            apply_mount_preferences(
                context,
                "codex",
                _build_parsed(docker_socket=True),
                mock.Mock(),
                confirm_persist,
            )

        self.assertTrue(agent_cfg.mounts.docker)

    def test_apply_mount_preferences_skips_docker_prompt_when_already_decided(
        self,
    ) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts(docker=False))
        context = _build_context(agent_cfg)

        confirm_persist = mock.Mock()

        with mock.patch(f"{_MODULE}.resolve_mount_prompt_prefs", return_value=None):
            apply_mount_preferences(
                context,
                "codex",
                _build_parsed(docker_socket=True),
                mock.Mock(),
                confirm_persist,
            )

        confirm_persist.assert_not_called()


def _build_context(agent_cfg: AgentConfig) -> ConfigContext:
    project_cfg = _ProjectConfig(path="/test-tmp/project", agents={"codex": agent_cfg})
    return ConfigContext(
        store=mock.Mock(),
        project_cfg=project_cfg,
        agents={},
        bases={},
        extensions={},
    )


def _build_parsed(docker_socket: bool = False) -> ParsedArgs:
    return ParsedArgs(False, "", "codex", [], docker_socket, [], None)
