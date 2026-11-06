from pathlib import Path, PurePosixPath
from unittest import TestCase, mock

from aicage.config.project_config import AgentConfig, _AgentMounts
from aicage.runtime.credential_agent import _resources, forwarding
from aicage.runtime.run_args import EnvVar, MountSpec, VolumeMountSpec


class CredentialAgentForwardingTests(TestCase):
    def test_ensure_ssh_setup_creates_only_a_required_sidecar(self) -> None:
        context = self._context(ssh=True)
        ssh_home = Path("/test-tmp/.ssh")
        with (
            mock.patch.object(
                forwarding, "_ssh_forwarding", return_value=([], [], True)
            ),
            mock.patch.object(forwarding, "HOST_SSH_DIR", ssh_home),
            mock.patch.object(Path, "is_dir", return_value=True),
            mock.patch.object(forwarding, "_ensure_sidecars") as ensure_mock,
        ):
            forwarding.ensure_ssh_setup(context, "codex", mock.Mock())

        ensure_mock.assert_called_once_with(
            [_resources._CredentialProtocol.SSH],
            mock.ANY,
            mock.ANY,
            {_resources._CredentialProtocol.SSH: ssh_home},
        )

    def test_forwarding_uses_direct_ssh_socket_when_available(self) -> None:
        socket = Path("/test-tmp/ssh-agent.sock")
        public_key = Path("/test-tmp/id_ed25519.pub")
        context = self._context(ssh=True)
        with (
            mock.patch.object(forwarding, "_direct_ssh_socket", return_value=socket),
            mock.patch.object(
                forwarding, "_resolve_ssh_support_files", return_value=[public_key]
            ),
            mock.patch.object(forwarding, "_ensure_sidecars") as ensure_mock,
        ):
            with forwarding.forwarding(context, "codex", mock.Mock()) as (mounts, env):
                self.assertEqual(
                    [
                        MountSpec(
                            socket,
                            PurePosixPath(
                                "/run/aicage-credential-agent/ssh-agent.sock"
                            ),
                        ),
                        MountSpec(
                            public_key, PurePosixPath("/test-tmp/id_ed25519.pub"), True
                        ),
                    ],
                    mounts,
                )
                self.assertEqual(
                    [
                        EnvVar(
                            "SSH_AUTH_SOCK",
                            "/run/aicage-credential-agent/ssh-agent.sock",
                        )
                    ],
                    env,
                )

        ensure_mock.assert_called_once_with([], mock.ANY, mock.ANY, {})

    def test_forwarding_uses_ssh_sidecar_on_windows_without_a_named_pipe_mount(
        self,
    ) -> None:
        resource = _resources._resources([_resources._CredentialProtocol.SSH])[0]
        ssh_home = Path("/test-tmp/.ssh")
        context = self._context(ssh=True)
        with (
            mock.patch.object(forwarding.os, "name", "nt"),
            mock.patch.object(forwarding, "HOST_SSH_DIR", ssh_home),
            mock.patch.object(Path, "is_dir", return_value=True),
            mock.patch.object(
                forwarding,
                "_resolve_ssh_key_files",
                return_value=[ssh_home / "id_ed25519"],
            ),
            mock.patch.object(
                forwarding, "_resolve_ssh_support_files", return_value=[]
            ),
            mock.patch.object(
                forwarding, "_ensure_sidecars", return_value=[resource]
            ) as ensure_mock,
        ):
            with forwarding.forwarding(context, "codex", mock.Mock()) as (mounts, env):
                self.assertEqual(
                    [
                        VolumeMountSpec(
                            "aicage-ssh-agent-socket",
                            PurePosixPath("/run/aicage-credential-agent"),
                            True,
                        )
                    ],
                    mounts,
                )
                self.assertEqual(
                    [
                        EnvVar(
                            "SSH_AUTH_SOCK",
                            "/run/aicage-credential-agent/ssh-agent.sock",
                        )
                    ],
                    env,
                )

        ensure_mock.assert_called_once_with(
            [_resources._CredentialProtocol.SSH],
            "0:0",
            mock.ANY,
            {_resources._CredentialProtocol.SSH: ssh_home},
        )

    def test_forwarding_uses_gpg_sidecar_and_preserves_public_files(self) -> None:
        resource = _resources._resources([_resources._CredentialProtocol.GPG])[0]
        gpg_home = Path("/test-tmp/gnupg")
        public_keyring = gpg_home / "pubring.kbx"
        context = self._context(gnupg=True)
        with (
            mock.patch.object(
                forwarding, "is_commit_signing_enabled", return_value=True
            ),
            mock.patch.object(
                forwarding, "resolve_signing_format", return_value="openpgp"
            ),
            mock.patch.object(forwarding, "resolve_gpg_home", return_value=gpg_home),
            mock.patch.object(
                forwarding, "resolve_gpg_public_files", return_value=[public_keyring]
            ),
            mock.patch.object(forwarding, "_direct_gpg_socket", return_value=None),
            mock.patch.object(
                forwarding, "_ensure_sidecars", return_value=[resource]
            ) as ensure_mock,
        ):
            with forwarding.forwarding(context, "codex", mock.Mock()) as (mounts, env):
                self.assertEqual(
                    [
                        MountSpec(
                            public_keyring,
                            PurePosixPath("/test-tmp/gnupg/pubring.kbx"),
                            True,
                        ),
                        VolumeMountSpec(
                            "aicage-gpg-agent-socket",
                            PurePosixPath("/test-tmp/gnupg"),
                            True,
                        ),
                    ],
                    mounts,
                )
                self.assertEqual([EnvVar("GNUPGHOME", "/test-tmp/gnupg")], env)

        ensure_mock.assert_called_once_with(
            [_resources._CredentialProtocol.GPG],
            mock.ANY,
            mock.ANY,
            {_resources._CredentialProtocol.GPG: gpg_home},
        )

    def test_forwarding_uses_direct_gpg_socket_when_available(self) -> None:
        gpg_home = Path("/test-tmp/gnupg")
        socket = Path("/test-tmp/S.gpg-agent.extra")
        public_keyring = gpg_home / "pubring.kbx"
        context = self._context(gnupg=True)
        with (
            mock.patch.object(
                forwarding, "is_commit_signing_enabled", return_value=True
            ),
            mock.patch.object(
                forwarding, "resolve_signing_format", return_value="openpgp"
            ),
            mock.patch.object(forwarding, "resolve_gpg_home", return_value=gpg_home),
            mock.patch.object(
                forwarding, "resolve_gpg_public_files", return_value=[public_keyring]
            ),
            mock.patch.object(forwarding, "_direct_gpg_socket", return_value=socket),
            mock.patch.object(forwarding, "_ensure_sidecars") as ensure_mock,
        ):
            with forwarding.forwarding(context, "codex", mock.Mock()) as (mounts, env):
                self.assertEqual(
                    [
                        MountSpec(socket, PurePosixPath("/test-tmp/gnupg/S.gpg-agent")),
                        MountSpec(
                            public_keyring,
                            PurePosixPath("/test-tmp/gnupg/pubring.kbx"),
                            True,
                        ),
                    ],
                    mounts,
                )
                self.assertEqual([EnvVar("GNUPGHOME", "/test-tmp/gnupg")], env)

        ensure_mock.assert_called_once_with([], mock.ANY, mock.ANY, {})

    @staticmethod
    def _context(*, ssh: bool = False, gnupg: bool = False) -> mock.Mock:
        context = mock.Mock()
        context.project_cfg.path = "/test-tmp/project"
        context.project_cfg.agents = {
            "codex": AgentConfig(mounts=_AgentMounts(ssh=ssh, gnupg=gnupg))
        }
        return context
