from pathlib import Path, PurePosixPath
from unittest import TestCase, mock

from aicage.config.project_config import AgentConfig, _AgentMounts
from aicage.runtime.credential_agent import forwarding
from aicage.runtime.credential_agent._resource_models import _CredentialProtocol, _resources
from aicage.runtime.run_args import EnvVar, VolumeMountSpec


class CredentialAgentForwardingTests(TestCase):
    def test_forwarding_ensures_ssh_sidecar_and_adds_target_args(self) -> None:
        resource = _resources([_CredentialProtocol.SSH])[0]
        context = mock.Mock()
        context.project_cfg.path = "/test-tmp/project"
        context.project_cfg.agents = {"codex": AgentConfig(mounts=_AgentMounts(ssh=True))}
        ssh_home = Path("/test-tmp/.ssh")
        with (
            mock.patch.object(forwarding, "_ssh_forwarding", return_value=([], [], True)),
            mock.patch.object(forwarding, "HOST_SSH_DIR", ssh_home),
            mock.patch.object(Path, "is_dir", return_value=True),
            mock.patch.object(forwarding, "_ensure_sidecars", return_value=[resource]) as ensure_mock,
            mock.patch.object(forwarding, "_reload_ssh_keys"),
        ):
            with forwarding.forwarding(context, "codex", mock.Mock()) as (mounts, env):
                self.assertEqual(
                    [VolumeMountSpec(resource.volume_name, PurePosixPath("/run/aicage-credential-agent"), True)], mounts
                )
                self.assertEqual([EnvVar("SSH_AUTH_SOCK", "/run/aicage-credential-agent/ssh-agent.sock")], env)

        ensure_mock.assert_called_once_with(
            [_CredentialProtocol.SSH], mock.ANY, mock.ANY, {_CredentialProtocol.SSH: ssh_home}
        )

    def test_ensure_ssh_setup_creates_the_required_sidecar(self) -> None:
        context = mock.Mock()
        context.project_cfg.agents = {"codex": AgentConfig(mounts=_AgentMounts(ssh=True))}
        ssh_home = Path("/test-tmp/.ssh")
        with (
            mock.patch.object(forwarding, "_ssh_forwarding", return_value=([], [], True)),
            mock.patch.object(forwarding, "HOST_SSH_DIR", ssh_home),
            mock.patch.object(Path, "is_dir", return_value=True),
            mock.patch.object(forwarding, "_ensure_sidecars") as ensure_mock,
            mock.patch.object(forwarding, "_reload_ssh_keys"),
        ):
            forwarding.ensure_ssh_setup(context, "codex", mock.Mock(), interactive=True)

        ensure_mock.assert_called_once_with(
            [_CredentialProtocol.SSH], mock.ANY, mock.ANY, {_CredentialProtocol.SSH: ssh_home}
        )

    def test_forwarding_ensures_gpg_sidecar_and_adds_target_args(self) -> None:
        resource = _resources([_CredentialProtocol.GPG])[0]
        context = mock.Mock()
        context.project_cfg.path = "/test-tmp/project"
        context.project_cfg.agents = {"codex": AgentConfig(mounts=_AgentMounts(gnupg=True))}
        gpg_home = Path("/test-tmp/gnupg")
        with (
            mock.patch.object(forwarding, "_gpg_enabled", return_value=True),
            mock.patch.object(
                forwarding,
                "_gpg_forwarding",
                return_value=([], [EnvVar("GNUPGHOME", "/test-tmp/gnupg")], True, gpg_home),
            ),
            mock.patch.object(forwarding, "_ensure_sidecars", return_value=[resource]) as ensure_mock,
            mock.patch.object(forwarding, "_reload_ssh_keys"),
        ):
            with forwarding.forwarding(context, "codex", mock.Mock()) as (mounts, _env):
                self.assertEqual(
                    [VolumeMountSpec(resource.volume_name, PurePosixPath("/test-tmp/gnupg"), True)], mounts
                )

        ensure_mock.assert_called_once_with(
            [_CredentialProtocol.GPG], mock.ANY, mock.ANY, {_CredentialProtocol.GPG: gpg_home}
        )
