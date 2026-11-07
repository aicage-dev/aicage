from pathlib import Path, PurePosixPath
from unittest import TestCase, mock

from aicage.runtime.credential_agent import _gpg_forwarding
from aicage.runtime.run_args import EnvVar, MountSpec


class GpgForwardingTests(TestCase):
    def test_gpg_forwarding_returns_empty_without_a_home(self) -> None:
        with mock.patch.object(_gpg_forwarding, "resolve_gpg_home", return_value=None):
            self.assertEqual(([], [], False, None), _gpg_forwarding._gpg_forwarding())

    def test_gpg_enabled_requires_openpgp_signing(self) -> None:
        context = mock.Mock()
        context.project_cfg.path = "/test-tmp/project"
        context.project_cfg.agents = {"codex": mock.Mock(mounts=mock.Mock(gnupg=True))}
        with (
            mock.patch.object(_gpg_forwarding, "is_commit_signing_enabled", return_value=True),
            mock.patch.object(_gpg_forwarding, "resolve_signing_format", return_value="openpgp"),
        ):
            self.assertTrue(_gpg_forwarding._gpg_enabled(context, "codex"))

    def test_direct_gpg_socket_requires_a_reachable_unix_socket(self) -> None:
        socket = mock.Mock(spec=Path)
        socket.is_socket.return_value = True
        with (
            mock.patch.object(_gpg_forwarding, "resolve_gpg_agent_extra_socket", return_value=socket),
            mock.patch.object(_gpg_forwarding, "_GPG_CONNECT_AGENT", "/usr/bin/gpg-connect-agent"),
            mock.patch.object(_gpg_forwarding.subprocess, "run", return_value=mock.Mock(returncode=0)),
        ):
            self.assertIs(socket, _gpg_forwarding._direct_gpg_socket())

    def test_gpg_forwarding_uses_a_sidecar_without_a_direct_socket(self) -> None:
        home = Path("/test-tmp/gnupg")
        with (
            mock.patch.object(_gpg_forwarding, "resolve_gpg_home", return_value=home),
            mock.patch.object(_gpg_forwarding, "resolve_gpg_public_files", return_value=[]),
            mock.patch.object(_gpg_forwarding, "_direct_gpg_socket", return_value=None),
        ):
            _mounts, _env, sidecar, actual_home = _gpg_forwarding._gpg_forwarding()

        self.assertTrue(sidecar)
        self.assertEqual(home, actual_home)

    def test_direct_gpg_socket_rejects_windows_and_missing_sockets(self) -> None:
        with mock.patch.object(_gpg_forwarding.os, "name", "nt"):
            self.assertIsNone(_gpg_forwarding._direct_gpg_socket())
        with mock.patch.object(_gpg_forwarding, "resolve_gpg_agent_extra_socket", return_value=None):
            self.assertIsNone(_gpg_forwarding._direct_gpg_socket())

    def test_gpg_forwarding_uses_direct_socket_and_public_files(self) -> None:
        home = Path("/test-tmp/gnupg")
        socket = home / "S.gpg-agent.extra"
        public_keyring = home / "pubring.kbx"
        with (
            mock.patch.object(_gpg_forwarding, "resolve_gpg_home", return_value=home),
            mock.patch.object(_gpg_forwarding, "resolve_gpg_public_files", return_value=[public_keyring]),
            mock.patch.object(_gpg_forwarding, "_direct_gpg_socket", return_value=socket),
        ):
            mounts, env, sidecar, actual_home = _gpg_forwarding._gpg_forwarding()
        self.assertEqual(
            [
                MountSpec(socket, PurePosixPath("/test-tmp/gnupg/S.gpg-agent")),
                MountSpec(public_keyring, PurePosixPath("/test-tmp/gnupg/pubring.kbx"), True),
            ],
            mounts,
        )
        self.assertEqual([EnvVar("GNUPGHOME", "/test-tmp/gnupg")], env)
        self.assertFalse(sidecar)
        self.assertEqual(home, actual_home)
