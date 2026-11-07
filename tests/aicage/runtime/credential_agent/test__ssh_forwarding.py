from pathlib import Path, PurePosixPath
from unittest import TestCase, mock

from aicage.runtime.credential_agent import _ssh_forwarding
from aicage.runtime.credential_agent._resource_models import _CredentialProtocol, _resources
from aicage.runtime.run_args import EnvVar, MountSpec, VolumeMountSpec


class SshForwardingTests(TestCase):
    def test_ssh_forwarding_skips_sidecar_without_keys_or_ssh_home(self) -> None:
        with (
            mock.patch.object(_ssh_forwarding, "_direct_ssh_socket", return_value=None),
            mock.patch.object(_ssh_forwarding, "_resolve_ssh_key_files", return_value=[]),
            mock.patch.object(_ssh_forwarding, "_resolve_ssh_support_files", return_value=[]),
            mock.patch.object(Path, "is_dir", return_value=False),
        ):
            self.assertEqual(([], [], False), _ssh_forwarding._ssh_forwarding())

    def test_ssh_forwarding_uses_a_sidecar_for_ssh_keys_or_home(self) -> None:
        with (
            mock.patch.object(_ssh_forwarding, "_direct_ssh_socket", return_value=None),
            mock.patch.object(_ssh_forwarding, "_resolve_ssh_key_files", return_value=[Path("/test-tmp/id_ed25519")]),
            mock.patch.object(_ssh_forwarding, "_resolve_ssh_support_files", return_value=[]),
        ):
            self.assertEqual(([], [], True), _ssh_forwarding._ssh_forwarding())

    def test_direct_ssh_socket_requires_a_reachable_unix_socket(self) -> None:
        socket = mock.Mock(spec=Path)
        socket.is_socket.return_value = True
        with (
            mock.patch.object(_ssh_forwarding, "_resolve_ssh_agent_socket", return_value=socket),
            mock.patch.object(_ssh_forwarding, "_agent_is_reachable", return_value=True),
        ):
            self.assertIs(socket, _ssh_forwarding._direct_ssh_socket())

    def test_direct_ssh_socket_rejects_missing_or_unreachable_sockets(self) -> None:
        with mock.patch.object(_ssh_forwarding, "_resolve_ssh_agent_socket", return_value=None):
            self.assertIsNone(_ssh_forwarding._direct_ssh_socket())

    def test_direct_ssh_socket_is_unavailable_on_windows(self) -> None:
        with mock.patch.object(_ssh_forwarding.os, "name", "nt"):
            self.assertIsNone(_ssh_forwarding._direct_ssh_socket())

        socket = mock.Mock(spec=Path)
        socket.is_socket.return_value = True
        with (
            mock.patch.object(_ssh_forwarding, "_resolve_ssh_agent_socket", return_value=socket),
            mock.patch.object(_ssh_forwarding, "_agent_is_reachable", return_value=False),
        ):
            self.assertIsNone(_ssh_forwarding._direct_ssh_socket())

    def test_ssh_forwarding_uses_direct_socket_when_available(self) -> None:
        socket = Path("/test-tmp/ssh-agent.sock")
        public_key = Path("/test-tmp/id_ed25519.pub")
        with (
            mock.patch.object(_ssh_forwarding, "_direct_ssh_socket", return_value=socket),
            mock.patch.object(_ssh_forwarding, "_resolve_ssh_support_files", return_value=[public_key]),
        ):
            mounts, env, sidecar = _ssh_forwarding._ssh_forwarding()
        self.assertEqual(
            [
                MountSpec(socket, PurePosixPath("/run/aicage-credential-agent/ssh-agent.sock")),
                MountSpec(public_key, PurePosixPath("/test-tmp/id_ed25519.pub"), True),
            ],
            mounts,
        )
        self.assertEqual([EnvVar("SSH_AUTH_SOCK", "/run/aicage-credential-agent/ssh-agent.sock")], env)
        self.assertFalse(sidecar)

    def test_append_ssh_target_args_adds_socket_volume_and_environment(self) -> None:
        resource = _resources([_CredentialProtocol.SSH])[0]
        mounts: list[MountSpec | VolumeMountSpec] = []
        env: list[EnvVar] = []
        _ssh_forwarding._append_ssh_target_args(resource, mounts, env)
        self.assertEqual(
            [VolumeMountSpec(resource.volume_name, PurePosixPath("/run/aicage-credential-agent"), True)], mounts
        )
        self.assertEqual([EnvVar("SSH_AUTH_SOCK", "/run/aicage-credential-agent/ssh-agent.sock")], env)

    def test_reload_ssh_keys_loads_unencrypted_key_from_sidecar_mount(self) -> None:
        resource = _resources([_CredentialProtocol.SSH])[0]
        key = Path("/test-tmp/.ssh/id_ed25519")
        with (
            mock.patch.object(_ssh_forwarding, "HOST_SSH_DIR", key.parent),
            mock.patch.object(_ssh_forwarding, "_resolve_ssh_key_files", return_value=[key]),
            mock.patch.object(_ssh_forwarding, "_ssh_key_is_encrypted", return_value=False),
            mock.patch.object(_ssh_forwarding, "_load_ssh_key") as load_mock,
        ):
            _ssh_forwarding._reload_ssh_keys([resource], interactive=False)
        load_mock.assert_called_once_with(resource, resource.credential_directory / "id_ed25519", "")

    def test_reload_ssh_keys_skips_missing_and_rejects_external_resources(self) -> None:
        resource = _resources([_CredentialProtocol.GPG])[0]
        _ssh_forwarding._reload_ssh_keys([resource], interactive=False)

        ssh_resource = _resources([_CredentialProtocol.SSH])[0]
        with (
            mock.patch.object(_ssh_forwarding, "_resolve_ssh_key_files", return_value=[Path("/outside/key")]),
            mock.patch.object(_ssh_forwarding, "HOST_SSH_DIR", Path("/test-tmp/.ssh")),
            self.assertRaisesRegex(RuntimeError, "outside"),
        ):
            _ssh_forwarding._reload_ssh_keys([ssh_resource], interactive=False)

    def test_ssh_passphrase_uses_stored_keyring_secret(self) -> None:
        key = Path("/test-tmp/.ssh/id_ed25519")
        with (
            mock.patch.object(_ssh_forwarding, "_ssh_key_is_encrypted", return_value=True),
            mock.patch.object(_ssh_forwarding, "_ssh_key_fingerprint", return_value="SHA256:key"),
            mock.patch.object(_ssh_forwarding, "get_secret", return_value="secret") as get_mock,
        ):
            actual = _ssh_forwarding._ssh_passphrase(key, interactive=False)

        self.assertEqual("secret", actual)
        get_mock.assert_called_once_with("aicage/ssh/passphrase/SHA256:key")

    def test_ssh_passphrase_requires_interactive_setup_for_a_missing_secret(self) -> None:
        key = Path("/test-tmp/.ssh/id_ed25519")
        with (
            mock.patch.object(_ssh_forwarding, "_ssh_key_is_encrypted", return_value=True),
            mock.patch.object(_ssh_forwarding, "_ssh_key_fingerprint", return_value="SHA256:key"),
            mock.patch.object(
                _ssh_forwarding,
                "get_secret",
                side_effect=_ssh_forwarding.SecretNotFoundError(),
            ),
            mock.patch.object(_ssh_forwarding.sys.stdin, "isatty", return_value=False),
        ):
            with self.assertRaisesRegex(RuntimeError, "Open the terminal configuration UI"):
                _ssh_forwarding._ssh_passphrase(key, interactive=False)

    def test_ssh_passphrase_stores_an_interactive_secret(self) -> None:
        key = Path("/test-tmp/.ssh/id_ed25519")
        with (
            mock.patch.object(_ssh_forwarding, "_ssh_key_is_encrypted", return_value=True),
            mock.patch.object(_ssh_forwarding, "_ssh_key_fingerprint", return_value="SHA256:key"),
            mock.patch.object(_ssh_forwarding, "get_secret", side_effect=_ssh_forwarding.SecretNotFoundError()),
            mock.patch.object(_ssh_forwarding.sys.stdin, "isatty", return_value=True),
            mock.patch.object(_ssh_forwarding, "getpass", return_value="secret"),
            mock.patch.object(_ssh_forwarding, "set_secret") as set_mock,
        ):
            self.assertEqual("secret", _ssh_forwarding._ssh_passphrase(key, interactive=True))

        set_mock.assert_called_once_with("aicage/ssh/passphrase/SHA256:key", "secret")

    def test_ssh_passphrase_rejects_an_empty_interactive_secret(self) -> None:
        key = Path("/test-tmp/.ssh/id_ed25519")
        with (
            mock.patch.object(_ssh_forwarding, "_ssh_key_is_encrypted", return_value=True),
            mock.patch.object(_ssh_forwarding, "_ssh_key_fingerprint", return_value="SHA256:key"),
            mock.patch.object(_ssh_forwarding, "get_secret", side_effect=_ssh_forwarding.SecretNotFoundError()),
            mock.patch.object(_ssh_forwarding.sys.stdin, "isatty", return_value=True),
            mock.patch.object(_ssh_forwarding, "getpass", return_value=""),
            self.assertRaisesRegex(RuntimeError, "No passphrase was supplied"),
        ):
            _ssh_forwarding._ssh_passphrase(key, interactive=True)

    def test_ssh_passphrase_translates_keyring_errors(self) -> None:
        key = Path("/test-tmp/.ssh/id_ed25519")
        with (
            mock.patch.object(_ssh_forwarding, "_ssh_key_is_encrypted", return_value=True),
            mock.patch.object(_ssh_forwarding, "_ssh_key_fingerprint", return_value="SHA256:key"),
            mock.patch.object(_ssh_forwarding, "get_secret", side_effect=_ssh_forwarding.KeyringError()),
            self.assertRaisesRegex(RuntimeError, "Cannot access the platform keyring"),
        ):
            _ssh_forwarding._ssh_passphrase(key, interactive=False)

    def test_ssh_key_helpers_interpret_command_results(self) -> None:
        key = Path("/test-tmp/id_ed25519")
        with (
            mock.patch.object(_ssh_forwarding, "_ssh_keygen", return_value="/usr/bin/ssh-keygen"),
            mock.patch.object(
                _ssh_forwarding.subprocess,
                "run",
                side_effect=[mock.Mock(returncode=1), mock.Mock(returncode=0, stdout="256 SHA256:key comment")],
            ),
            mock.patch.object(Path, "is_file", return_value=False),
        ):
            self.assertTrue(_ssh_forwarding._ssh_key_is_encrypted(key))
            self.assertEqual("SHA256:key", _ssh_forwarding._ssh_key_fingerprint(key))

    def test_ssh_keygen_requires_the_host_tool(self) -> None:
        with (
            mock.patch.object(_ssh_forwarding, "_SSH_KEYGEN", None),
            self.assertRaisesRegex(RuntimeError, "ssh-keygen is required"),
        ):
            _ssh_forwarding._ssh_keygen()

    def test_ssh_keygen_returns_the_absolute_host_tool_path(self) -> None:
        with mock.patch.object(_ssh_forwarding, "_SSH_KEYGEN", "/usr/bin/ssh-keygen"):
            self.assertEqual("/usr/bin/ssh-keygen", _ssh_forwarding._ssh_keygen())

    def test_ssh_key_fingerprint_rejects_invalid_command_output(self) -> None:
        key = Path("/test-tmp/id_ed25519")
        with (
            mock.patch.object(_ssh_forwarding, "_ssh_keygen", return_value="/usr/bin/ssh-keygen"),
            mock.patch.object(_ssh_forwarding.subprocess, "run", return_value=mock.Mock(returncode=1, stdout="")),
            self.assertRaisesRegex(RuntimeError, "Cannot determine the fingerprint"),
        ):
            _ssh_forwarding._ssh_key_fingerprint(key)
