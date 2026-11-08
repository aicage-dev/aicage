from contextlib import nullcontext
from pathlib import Path, PurePosixPath
from unittest import TestCase, mock

from aicage.config.project_config import AgentConfig, _AgentMounts
from aicage.runtime.credential_agent import _gpg_forwarding, forwarding
from aicage.runtime.credential_agent._resource_models import (
    _CredentialProtocol,
    _resources,
)
from aicage.runtime.run_args import EnvVar, VolumeMountSpec


class CredentialAgentForwardingTests(TestCase):
    def test_prepare_credentials_ensures_all_requested_sidecars_once(self) -> None:
        ssh_resource, gpg_resource = _resources(
            [_CredentialProtocol.SSH, _CredentialProtocol.GPG]
        )
        context = mock.Mock()
        context.project_cfg.agents = {
            "codex": AgentConfig(mounts=_AgentMounts(ssh=True, gnupg=True))
        }
        gpg_plan = _gpg_forwarding._GpgForwardingPlan(Path("/test-tmp/gnupg"), True)
        with (
            mock.patch.object(
                forwarding, "_ssh_forwarding", return_value=([], [], True)
            ),
            mock.patch.object(forwarding, "_gpg_enabled", return_value=True),
            mock.patch.object(forwarding, "_gpg_forwarding", return_value=gpg_plan),
            mock.patch.object(
                forwarding, "_credential_image", return_value=("image", "id")
            ) as image_mock,
            mock.patch.object(
                forwarding,
                "_ensure_resources",
                return_value=[ssh_resource, gpg_resource],
            ) as resources_mock,
        ):
            forwarding.prepare_credentials(
                context, "codex", mock.Mock(), interactive=True
            )

        image_mock.assert_called_once()
        resources_mock.assert_called_once_with(
            [_CredentialProtocol.SSH, _CredentialProtocol.GPG],
            mock.ANY,
            gpg_plan.credential_home,
            reconcile=mock.ANY,
        )

    def test_credential_forwarding_adds_ssh_target_args(self) -> None:
        resource = _resources([_CredentialProtocol.SSH])[0]
        setup = forwarding.CredentialSetup(
            forwarding._CredentialPlan([], [], [_CredentialProtocol.SSH], None),
            [resource],
        )
        with forwarding.credential_forwarding(setup) as (mounts, env):
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
                [EnvVar("SSH_AUTH_SOCK", "/run/credential-agent/ssh-agent.sock")],
                env,
            )

    def test_credential_forwarding_uses_direct_gpg_target_args(self) -> None:
        gpg_plan = _gpg_forwarding._GpgForwardingPlan(
            Path("/test-tmp/gnupg"), False, Path("/test-tmp/gnupg/S.gpg-agent")
        )
        setup = forwarding.CredentialSetup(
            forwarding._CredentialPlan([], [], [], gpg_plan), []
        )
        with mock.patch.object(
            gpg_plan, "direct_target_args", return_value=nullcontext([])
        ):
            with forwarding.credential_forwarding(setup) as (mounts, env):
                self.assertEqual([], mounts)
                self.assertEqual([], env)
