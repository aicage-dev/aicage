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
            reconcile=mock.ANY,
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
            reconcile=mock.ANY,
        )

    def test_ensure_gpg_setup_passes_a_reconciler_to_a_fallback_sidecar(self) -> None:
        resource = _resources([_CredentialProtocol.GPG])[0]
        context = mock.Mock()
        context.project_cfg.path = "/test-tmp/project"
        context.project_cfg.agents = {
            "codex": AgentConfig(mounts=_AgentMounts(gnupg=True))
        }
        plan = _gpg_forwarding._GpgForwardingPlan(Path("/test-tmp/gnupg"), [], [], True)
        with (
            mock.patch.object(forwarding, "_gpg_enabled", return_value=True),
            mock.patch.object(forwarding, "_gpg_forwarding", return_value=plan),
            mock.patch.object(
                forwarding, "_ensure_sidecars", return_value=[resource]
            ) as ensure_mock,
        ):
            forwarding.ensure_gpg_setup(context, "codex", mock.Mock(), interactive=True)

        ensure_mock.assert_called_once_with(
            [_CredentialProtocol.GPG],
            mock.ANY,
            mock.ANY,
            plan.credential_home,
            reconcile=mock.ANY,
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
            mock.patch.object(forwarding, "_reload_gpg_keys"),
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
            reconcile=mock.ANY,
        )

    def test_reload_credentials_reloads_both_protocols(self) -> None:
        resources = _resources([_CredentialProtocol.SSH, _CredentialProtocol.GPG])
        with (
            mock.patch.object(forwarding, "_reload_ssh_keys") as ssh_reload,
            mock.patch.object(forwarding, "_reload_gpg_keys") as gpg_reload,
        ):
            forwarding._reload_credentials(resources, interactive=True)

        ssh_reload.assert_called_once_with(resources, interactive=True)
        gpg_reload.assert_called_once_with(resources, interactive=True)
