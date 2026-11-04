from pathlib import Path, PurePosixPath
from unittest import TestCase, mock

from aicage.config.project_config import AgentConfig, _AgentMounts
from aicage.runtime.docker_args.resolvers import ssh_keys
from aicage.runtime.docker_args.support.resolver_types import MountRequest, ResolvedArgs
from aicage.runtime.run_args import EnvVar

from ._fixtures import build_context, build_parsed

_MODULE = "aicage.runtime.docker_args.resolvers.ssh_keys"
_CONTAINER_SOCKET = PurePosixPath("/run/aicage-ssh-agent.sock")
_AGENT_SOCKET = Path("/test-tmp/agent.sock")


class SshKeyTests(TestCase):
    def test_resolve_ssh_mount_skips_when_not_needed(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts(ssh=True))
        context = build_context(agent_cfg)
        with (
            mock.patch(f"{_MODULE}.is_commit_signing_enabled", return_value=False),
            mock.patch(f"{_MODULE}.uses_ssh_remotes", return_value=False),
        ):
            resolved = ssh_keys.resolve(context, "codex", build_parsed())
        self.assertEqual(ResolvedArgs(), resolved)

    def test_resolve_ssh_mount_skips_for_non_ssh_format(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts(ssh=True))
        context = build_context(agent_cfg)
        with (
            mock.patch(
                f"{_MODULE}.is_commit_signing_enabled",
                return_value=True,
            ),
            mock.patch(
                f"{_MODULE}.resolve_signing_format",
                return_value="gpg",
            ),
            mock.patch(f"{_MODULE}.uses_ssh_remotes", return_value=False),
        ):
            resolved = ssh_keys.resolve(context, "codex", build_parsed())
        self.assertEqual(ResolvedArgs(), resolved)

    def test_resolve_ssh_mount_respects_pref(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts(ssh=False))
        context = build_context(agent_cfg)
        with (
            mock.patch(f"{_MODULE}.is_commit_signing_enabled", return_value=True),
            mock.patch(f"{_MODULE}.resolve_signing_format", return_value="ssh"),
            mock.patch(f"{_MODULE}.uses_ssh_remotes", return_value=False),
            mock.patch(f"{_MODULE}.resolve_ssh_agent_socket", return_value=_AGENT_SOCKET),
        ):
            resolved = ssh_keys.resolve(context, "codex", build_parsed())
        self.assertEqual(ResolvedArgs(), resolved)

    def test_resolve_ssh_mount_uses_preference(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts(ssh=True))
        context = build_context(agent_cfg)
        config = Path("/test-tmp/.ssh/config")
        known_hosts = Path("/test-tmp/.ssh/known_hosts")
        with (
            mock.patch(f"{_MODULE}.is_commit_signing_enabled", return_value=True),
            mock.patch(f"{_MODULE}.resolve_signing_format", return_value="ssh"),
            mock.patch(f"{_MODULE}.uses_ssh_remotes", return_value=False),
            mock.patch(f"{_MODULE}.resolve_ssh_agent_socket", return_value=_AGENT_SOCKET),
            mock.patch(
                f"{_MODULE}.resolve_ssh_support_files",
                return_value=[config, known_hosts],
            ),
        ):
            resolved = ssh_keys.resolve(context, "codex", build_parsed())
        self.assertEqual(
            ResolvedArgs(
                mounts=[
                    MountRequest(host_path=_AGENT_SOCKET, container_path=_CONTAINER_SOCKET),
                    MountRequest(host_path=config, read_only=True),
                    MountRequest(host_path=known_hosts, read_only=True),
                ],
                env=[EnvVar(name="SSH_AUTH_SOCK", value=_CONTAINER_SOCKET.as_posix())],
            ),
            resolved,
        )

    def test_resolve_ssh_mount_uses_ssh_remotes(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts(ssh=True))
        context = build_context(agent_cfg)
        with (
            mock.patch(f"{_MODULE}.is_commit_signing_enabled", return_value=False),
            mock.patch(f"{_MODULE}.uses_ssh_remotes", return_value=True),
            mock.patch(f"{_MODULE}.resolve_ssh_agent_socket", return_value=_AGENT_SOCKET),
            mock.patch(f"{_MODULE}.resolve_ssh_support_files", return_value=[]),
        ):
            resolved = ssh_keys.resolve(context, "codex", build_parsed())
        self.assertEqual(
            ResolvedArgs(
                mounts=[MountRequest(host_path=_AGENT_SOCKET, container_path=_CONTAINER_SOCKET)],
                env=[EnvVar(name="SSH_AUTH_SOCK", value=_CONTAINER_SOCKET.as_posix())],
            ),
            resolved,
        )
