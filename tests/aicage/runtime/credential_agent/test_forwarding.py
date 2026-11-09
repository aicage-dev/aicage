from contextlib import nullcontext
from pathlib import Path, PurePosixPath
from unittest import TestCase, mock

from aicage.config.project_config import AgentConfig, _AgentMounts
from aicage.runtime.credential_agent import _gpg_forwarding, forwarding
from aicage.runtime.credential_agent._resource_models import (
    _CredentialProtocol,
    _resources,
)
from aicage.runtime.run_args import BindMountSpec, EnvVar, VolumeMountSpec


class CredentialAgentForwardingTests(TestCase):
    def test_forwarding_ensures_ssh_sidecar_and_adds_target_args(self) -> None:
        resource = _resources([_CredentialProtocol.SSH])[0]
        context = mock.Mock()
        context.project_cfg.path = "/test-tmp/project"
        context.project_cfg.agents = {
            "codex": AgentConfig(mounts=_AgentMounts(ssh=True))
        }
        with (
            mock.patch.object(
                forwarding, "_ssh_forwarding", return_value=([], [], True)
            ),
            mock.patch.object(
                forwarding, "_ensure_sidecars", return_value=[resource]
            ) as ensure_mock,
            mock.patch.object(forwarding, "_reload_ssh_keys"),
        ):
            with forwarding.forwarding(context, "codex", mock.Mock()) as (mounts, env):
                self.assertEqual(
                    [
                        VolumeMountSpec(
                            resource.volume_name,
                            PurePosixPath("/run/credential-agent"),
                            True,
                        )
                    ],
                    mounts,
                )
                self.assertEqual(
                    [
                        EnvVar(
                            "SSH_AUTH_SOCK",
                            "/run/credential-agent/ssh-agent.sock",
                        )
                    ],
                    env,
                )

        ensure_mock.assert_called_once_with(
            [_CredentialProtocol.SSH],
            mock.ANY,
            mock.ANY,
            None,
        )

    def test_ensure_ssh_setup_creates_the_required_sidecar(self) -> None:
        context = mock.Mock()
        context.project_cfg.agents = {
            "codex": AgentConfig(mounts=_AgentMounts(ssh=True))
        }
        with (
            mock.patch.object(
                forwarding, "_ssh_forwarding", return_value=([], [], True)
            ),
            mock.patch.object(
                forwarding, "_ensure_sidecars"
            ) as ensure_mock,
            mock.patch.object(forwarding, "_reload_ssh_keys"),
        ):
            forwarding.ensure_ssh_setup(context, "codex", mock.Mock(), interactive=True)

        ensure_mock.assert_called_once_with(
            [_CredentialProtocol.SSH],
            mock.ANY,
            mock.ANY,
        )

    def test_forwarding_ensures_gpg_sidecar_and_adds_target_args(self) -> None:
        resource = _resources([_CredentialProtocol.GPG])[0]
        context = mock.Mock()
        context.project_cfg.path = "/test-tmp/project"
        context.project_cfg.agents = {
            "codex": AgentConfig(mounts=_AgentMounts(gnupg=True))
        }
        gpg_home = Path("/test-tmp/gnupg")
        gpg_plan = _gpg_forwarding._GpgForwardingPlan(gpg_home, [], [], True)
        client_home = Path("/test-tmp/client-gnupg")
        target_home = PurePosixPath("/run/credential-agent-client/gnupg")
        with (
            mock.patch.object(forwarding, "_gpg_enabled", return_value=True),
            mock.patch.object(
                forwarding,
                "_gpg_forwarding",
                return_value=gpg_plan,
            ),
            mock.patch.object(
                _gpg_forwarding,
                "_gpg_sidecar_target_args",
                return_value=nullcontext(
                    (
                        [
                            BindMountSpec(client_home, target_home),
                            VolumeMountSpec(
                                resource.volume_name,
                                resource.socket_directory,
                                True,
                            ),
                        ],
                        [EnvVar("GNUPGHOME", target_home.as_posix())],
                    )
                ),
            ) as target_args_mock,
            mock.patch.object(
                forwarding, "_ensure_sidecars", return_value=[resource]
            ) as ensure_mock,
            mock.patch.object(forwarding, "_reload_ssh_keys"),
        ):
            with forwarding.forwarding(context, "codex", mock.Mock()) as (mounts, _env):
                self.assertEqual(
                    [
                        BindMountSpec(client_home, target_home),
                        VolumeMountSpec(
                            resource.volume_name,
                            resource.socket_directory,
                            True,
                        ),
                    ],
                    mounts,
                )
                self.assertEqual(
                    [EnvVar("GNUPGHOME", target_home.as_posix())], _env
                )

        target_args_mock.assert_called_once_with(resource, gpg_home)
        ensure_mock.assert_called_once_with(
            [_CredentialProtocol.GPG],
            mock.ANY,
            mock.ANY,
            gpg_home,
        )
