import tempfile
from pathlib import Path, PurePosixPath
from unittest import TestCase, mock

from aicage.cli_types import ParsedArgs
from aicage.config.agent.models import AgentMetadata
from aicage.config.base.models import BaseMetadata
from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig, ProjectConfig
from aicage.paths import CONTAINER_USER_HOME_MOUNTS_DIR, container_project_path
from aicage.runtime.docker_args import resolver
from aicage.runtime.docker_args._resolver_types import MountRequest, ResolvedArgs
from aicage.runtime.env_vars import AICAGE_WORKSPACE
from aicage.runtime.run_args import EnvVar, MountSpec


class ResolverTests(TestCase):
    def test_resolve_docker_args_aggregates_mounts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home_path = Path(temp_dir) / "home"
            project_path = Path(temp_dir) / "project"
            home_path.mkdir()
            project_path.mkdir()
            git_config = home_path / ".gitconfig"
            docker_sock = Path(temp_dir) / "docker.sock"

            project_cfg = ProjectConfig(path=str(project_path), agents={"codex": AgentConfig()})
            context = ConfigContext(
                store=mock.Mock(),
                project_cfg=project_cfg,
                agents=self._get_agents(),
                bases=self._get_bases(),
                extensions={},
            )
            parsed = ParsedArgs(False, "", "codex", [], False, [], None)

            with (
                mock.patch("aicage.runtime.docker_args.resolver.resolve_git_support_prefs") as git_support_mock,
                mock.patch(
                    "aicage.runtime.docker_args.resolver._project.resolve",
                    return_value=ResolvedArgs(mounts=[MountRequest(host_path=project_path)]),
                ),
                mock.patch("aicage.runtime.docker_args.resolver._agent_config.resolve", return_value=ResolvedArgs()),
                mock.patch(
                    "aicage.runtime.docker_args.resolver._git_config.resolve",
                    return_value=ResolvedArgs(mounts=[MountRequest(host_path=git_config)]),
                ) as git_mock,
                mock.patch("aicage.runtime.docker_args.resolver._git_root.resolve", return_value=ResolvedArgs()),
                mock.patch("aicage.runtime.docker_args.resolver._ssh_keys.resolve", return_value=ResolvedArgs()),
                mock.patch("aicage.runtime.docker_args.resolver._gpg.resolve", return_value=ResolvedArgs()),
                mock.patch(
                    "aicage.runtime.docker_args.resolver._docker_socket.resolve",
                    return_value=ResolvedArgs(
                        mounts=[MountRequest(host_path=docker_sock)],
                        env=[EnvVar(name="DOCKER_HOST", value="tcp://host:2375")],
                    ),
                ) as docker_mock,
                mock.patch("aicage.runtime.docker_args.resolver._shares.resolve", return_value=ResolvedArgs()),
                mock.patch("aicage.runtime.docker_args.resolver.Path.home", return_value=home_path),
            ):
                mounts, env = resolver.resolve_docker_args(context, "codex", parsed)

        self.assertEqual(
            [
                MountSpec(
                    host_path=project_path,
                    container_path=container_project_path(project_path),
                ),
                MountSpec(
                    host_path=git_config,
                    container_path=CONTAINER_USER_HOME_MOUNTS_DIR / PurePosixPath(".gitconfig"),
                ),
                MountSpec(
                    host_path=docker_sock,
                    container_path=container_project_path(docker_sock),
                ),
            ],
            mounts,
        )
        self.assertEqual(
            [
                ("DOCKER_HOST", "tcp://host:2375"),
                (AICAGE_WORKSPACE, container_project_path(project_path).as_posix()),
            ],
            [(item.name, item.value) for item in env],
        )
        git_support_mock.assert_called_once_with(project_path, project_cfg.agents["codex"])
        git_mock.assert_called_once_with(context, "codex", parsed)
        docker_mock.assert_called_once_with(context, "codex", parsed)

    def test_resolve_docker_args_inserts_agent_config(self) -> None:
        project_cfg = ProjectConfig(path="/tmp/project", agents={})
        context = ConfigContext(
            store=mock.Mock(),
            project_cfg=project_cfg,
            agents=self._get_agents(),
            bases=self._get_bases(),
            extensions={},
        )

        with (
            mock.patch("aicage.runtime.docker_args.resolver.resolve_git_support_prefs"),
            mock.patch("aicage.runtime.docker_args.resolver._project.resolve", return_value=ResolvedArgs()),
            mock.patch("aicage.runtime.docker_args.resolver._agent_config.resolve", return_value=ResolvedArgs()),
            mock.patch("aicage.runtime.docker_args.resolver._git_config.resolve", return_value=ResolvedArgs()),
            mock.patch("aicage.runtime.docker_args.resolver._git_root.resolve", return_value=ResolvedArgs()),
            mock.patch("aicage.runtime.docker_args.resolver._ssh_keys.resolve", return_value=ResolvedArgs()),
            mock.patch("aicage.runtime.docker_args.resolver._gpg.resolve", return_value=ResolvedArgs()),
            mock.patch("aicage.runtime.docker_args.resolver._docker_socket.resolve", return_value=ResolvedArgs()),
            mock.patch("aicage.runtime.docker_args.resolver._shares.resolve", return_value=ResolvedArgs()),
            mock.patch("aicage.runtime.docker_args.resolver.Path.home", return_value=Path("/tmp/home")),
        ):
            resolver.resolve_docker_args(context, "codex", None)

        self.assertIsInstance(project_cfg.agents["codex"], AgentConfig)

    def test_resolve_docker_args_uses_host_path_for_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home_path = Path(temp_dir) / "home"
            project_path = home_path / "project"
            home_path.mkdir()
            project_path.mkdir()

            project_cfg = ProjectConfig(path=str(project_path), agents={"codex": AgentConfig()})
            context = ConfigContext(
                store=mock.Mock(),
                project_cfg=project_cfg,
                agents=self._get_agents(),
                bases=self._get_bases(),
                extensions={},
            )
            parsed = ParsedArgs(False, "", "codex", [], False, [], None)

            with (
                mock.patch("aicage.runtime.docker_args.resolver.resolve_git_support_prefs"),
                mock.patch(
                    "aicage.runtime.docker_args.resolver._project.resolve",
                    return_value=ResolvedArgs(mounts=[MountRequest(host_path=project_path)]),
                ),
                mock.patch("aicage.runtime.docker_args.resolver._agent_config.resolve", return_value=ResolvedArgs()),
                mock.patch("aicage.runtime.docker_args.resolver._git_config.resolve", return_value=ResolvedArgs()),
                mock.patch("aicage.runtime.docker_args.resolver._git_root.resolve", return_value=ResolvedArgs()),
                mock.patch("aicage.runtime.docker_args.resolver._ssh_keys.resolve", return_value=ResolvedArgs()),
                mock.patch("aicage.runtime.docker_args.resolver._gpg.resolve", return_value=ResolvedArgs()),
                mock.patch("aicage.runtime.docker_args.resolver._docker_socket.resolve", return_value=ResolvedArgs()),
                mock.patch("aicage.runtime.docker_args.resolver._shares.resolve", return_value=ResolvedArgs()),
                mock.patch("aicage.runtime.docker_args.resolver.Path.home", return_value=home_path),
            ):
                mounts, env = resolver.resolve_docker_args(context, "codex", parsed)

        self.assertEqual(
            [
                MountSpec(
                    host_path=project_path,
                    container_path=CONTAINER_USER_HOME_MOUNTS_DIR / PurePosixPath("project"),
                )
            ],
            mounts,
        )
        self.assertEqual(
            [
                (AICAGE_WORKSPACE, container_project_path(project_path).as_posix()),
            ],
            [(item.name, item.value) for item in env],
        )

    @staticmethod
    def _get_bases() -> dict[str, BaseMetadata]:
        return {
            "ubuntu": BaseMetadata(
                from_image="ubuntu:latest",
                base_image_distro="Ubuntu",
                base_image_description="Default",
                build_local=False,
                local_definition_dir=Path("/tmp/base"),
            )
        }

    @staticmethod
    def _get_agents() -> dict[str, AgentMetadata]:
        return {
            "codex": AgentMetadata(
                agent_path=["~/.codex"],
                agent_full_name="Codex CLI",
                agent_homepage="https://example.com",
                build_local=False,
                valid_bases={"ubuntu": "ghcr.io/aicage/aicage:codex-ubuntu"},
                local_definition_dir=Path("/tmp/agent"),
            )
        }
