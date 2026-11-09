import tempfile
from pathlib import Path, PurePosixPath
from unittest import TestCase, mock

from aicage.paths import container_project_path
from aicage.runtime.credential_agent import _gpg_forwarding
from aicage.runtime.credential_agent._resource_models import (
    _CredentialProtocol,
    _resources,
)
from aicage.runtime.run_args import BindMountSpec, EnvVar, VolumeMountSpec


class GpgForwardingTests(TestCase):
    def test_gpg_forwarding_returns_none_without_a_home(self) -> None:
        with mock.patch.object(_gpg_forwarding, "resolve_gpg_home", return_value=None):
            self.assertIsNone(_gpg_forwarding._gpg_forwarding())

    def test_gpg_enabled_requires_openpgp_signing(self) -> None:
        context = mock.Mock()
        context.project_cfg.path = "/test-tmp/project"
        context.project_cfg.agents = {"codex": mock.Mock(mounts=mock.Mock(gnupg=True))}
        with (
            mock.patch.object(
                _gpg_forwarding, "is_commit_signing_enabled", return_value=True
            ),
            mock.patch.object(
                _gpg_forwarding, "resolve_signing_format", return_value="openpgp"
            ),
        ):
            self.assertTrue(_gpg_forwarding._gpg_enabled(context, "codex"))

    def test_direct_gpg_socket_requires_a_reachable_unix_socket(self) -> None:
        socket = mock.Mock(spec=Path)
        socket.is_socket.return_value = True
        with (
            mock.patch.object(_gpg_forwarding.os, "name", "posix"),
            mock.patch.object(
                _gpg_forwarding, "resolve_gpg_agent_socket", return_value=socket
            ),
            mock.patch.object(
                _gpg_forwarding, "_GPG_CONNECT_AGENT", "/usr/bin/gpg-connect-agent"
            ),
            mock.patch.object(
                _gpg_forwarding.subprocess, "run", return_value=mock.Mock(returncode=0)
            ),
        ):
            self.assertIs(socket, _gpg_forwarding._direct_gpg_socket())

    def test_gpg_forwarding_uses_a_sidecar_without_a_direct_socket(self) -> None:
        home = Path("/test-tmp/gnupg")
        with (
            mock.patch.object(_gpg_forwarding, "resolve_gpg_home", return_value=home),
            mock.patch.object(
                _gpg_forwarding, "resolve_gpg_public_files"
            ) as public_files_mock,
            mock.patch.object(_gpg_forwarding, "_direct_gpg_socket", return_value=None),
        ):
            plan = _gpg_forwarding._gpg_forwarding()

        assert plan is not None
        self.assertTrue(plan.requires_sidecar)
        self.assertEqual(home, plan.credential_home)
        public_files_mock.assert_not_called()

    def test_direct_gpg_socket_rejects_windows_and_missing_sockets(self) -> None:
        with mock.patch.object(_gpg_forwarding.os, "name", "nt"):
            self.assertIsNone(_gpg_forwarding._direct_gpg_socket())

    def test_sidecar_target_args_uses_a_private_client_home(self) -> None:
        resource = _resources([_CredentialProtocol.GPG])[0]
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            gpg_home = parent / "gnupg"
            gpg_home.mkdir()
            public_keyring = gpg_home / "pubring.kbx"
            external_keyring = parent / "external.kbx"
            public_keyring.write_text("public keyring", encoding="utf-8")
            external_keyring.write_text("external keyring", encoding="utf-8")
            with mock.patch.object(
                _gpg_forwarding,
                "resolve_gpg_public_files",
                return_value=[public_keyring, external_keyring],
            ):
                plan = _gpg_forwarding._GpgForwardingPlan(
                    gpg_home, [], [], True
                )
                with plan.sidecar_target_args(resource) as (mounts, env):
                    client_mount = mounts[0]
                    assert isinstance(client_mount, BindMountSpec)
                    client_home = client_mount.host_path
                    self.assertEqual(
                        "public keyring",
                        (client_home / "pubring.kbx").read_text(encoding="utf-8"),
                    )
                    self.assertEqual(
                        resource.socket_path.as_posix(),
                        (client_home / "S.gpg-agent").readlink().as_posix(),
                    )
                    self.assertEqual(
                        [
                            BindMountSpec(
                                client_home,
                                PurePosixPath("/run/credential-agent-client/gnupg"),
                            ),
                            BindMountSpec(
                                external_keyring,
                                container_project_path(external_keyring),
                                True,
                            ),
                            VolumeMountSpec(
                                resource.volume_name,
                                resource.socket_directory,
                                True,
                            ),
                        ],
                        mounts,
                    )
                    self.assertEqual(
                        [
                            EnvVar(
                                "GNUPGHOME",
                                "/run/credential-agent-client/gnupg",
                            )
                        ],
                        env,
                    )
            self.assertFalse(client_home.exists())
        with (
            mock.patch.object(_gpg_forwarding.os, "name", "posix"),
            mock.patch.object(
                _gpg_forwarding, "resolve_gpg_agent_socket", return_value=None
            ),
        ):
            self.assertIsNone(_gpg_forwarding._direct_gpg_socket())

    def test_gpg_forwarding_uses_direct_socket_and_public_files(self) -> None:
        home = Path("/test-tmp/gnupg")
        socket = home / "S.gpg-agent"
        public_keyring = home / "pubring.kbx"
        with (
            mock.patch.object(_gpg_forwarding, "resolve_gpg_home", return_value=home),
            mock.patch.object(
                _gpg_forwarding,
                "resolve_gpg_public_files",
                return_value=[public_keyring],
            ),
            mock.patch.object(
                _gpg_forwarding, "_direct_gpg_socket", return_value=socket
            ),
        ):
            plan = _gpg_forwarding._gpg_forwarding()
        assert plan is not None
        self.assertEqual(
            [
                BindMountSpec(socket, PurePosixPath("/test-tmp/gnupg/S.gpg-agent")),
                BindMountSpec(
                    public_keyring, PurePosixPath("/test-tmp/gnupg/pubring.kbx"), True
                ),
            ],
            plan.target_mounts,
        )
        self.assertEqual([EnvVar("GNUPGHOME", "/test-tmp/gnupg")], plan.target_env)
        self.assertFalse(plan.requires_sidecar)
        self.assertEqual(home, plan.credential_home)
