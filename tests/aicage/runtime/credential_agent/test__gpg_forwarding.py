import tempfile
from contextlib import nullcontext
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

    def test_gpg_enabled_requires_mount_preference(self) -> None:
        context = mock.Mock()
        context.project_cfg.agents = {"codex": mock.Mock(mounts=mock.Mock(gnupg=True))}
        self.assertTrue(_gpg_forwarding._gpg_enabled(context, "codex"))

        context.project_cfg.agents["codex"].mounts.gnupg = False
        self.assertFalse(_gpg_forwarding._gpg_enabled(context, "codex"))

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
                plan = _gpg_forwarding._GpgForwardingPlan(gpg_home, [], [], True)
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

    def test_gpg_forwarding_uses_a_direct_socket(self) -> None:
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
        self.assertEqual([], plan.target_mounts)
        self.assertEqual([], plan.target_env)
        self.assertFalse(plan.requires_sidecar)
        self.assertEqual(socket, plan.direct_socket)
        self.assertEqual(home, plan.credential_home)

    def test_direct_target_args_uses_the_direct_agent_socket(self) -> None:
        home = Path("/test-tmp/gnupg")
        socket = home / "S.gpg-agent"
        plan = _gpg_forwarding._GpgForwardingPlan(home, [], [], False, socket)
        expected = (
            [BindMountSpec(Path("/test-tmp/client"), PurePosixPath("/client"))],
            [EnvVar("GNUPGHOME", "/client")],
        )
        with mock.patch.object(
            _gpg_forwarding,
            "_gpg_direct_target_args",
            return_value=nullcontext(expected),
        ) as target_args:
            with plan.direct_target_args() as actual:
                self.assertEqual(expected, actual)

        target_args.assert_called_once_with(socket, home)

    def test_prepare_direct_gpg_keys_unlocks_each_secret_key(self) -> None:
        home = Path("/test-tmp/gnupg")
        with (
            mock.patch.object(_gpg_forwarding, "_GPG", "/usr/bin/gpg"),
            mock.patch.object(
                _gpg_forwarding,
                "resolve_gpg_secret_key_state",
                return_value=(["FIRST", "SECOND"], set()),
            ),
            mock.patch.object(
                _gpg_forwarding.subprocess,
                "run",
                return_value=mock.Mock(returncode=0),
            ) as run_mock,
        ):
            _gpg_forwarding._prepare_direct_gpg_keys(home)

        self.assertEqual(2, run_mock.call_count)
        for fingerprint, call in zip(
            ["FIRST", "SECOND"], run_mock.call_args_list, strict=True
        ):
            command = call.args[0]
            self.assertEqual("/usr/bin/gpg", command[0])
            self.assertEqual(["--homedir", str(home)], command[1:3])
            self.assertIn(fingerprint, command)
            self.assertIn("--detach-sign", command)
            self.assertFalse(call.kwargs["check"])

    def test_reload_gpg_keys_loads_protected_keys(self) -> None:
        resource = _resources([_CredentialProtocol.GPG])[0]
        with (
            mock.patch.object(
                _gpg_forwarding,
                "resolve_gpg_secret_key_state",
                return_value=(["FIRST", "SECOND"], {"ONE"}),
            ),
            mock.patch.object(_gpg_forwarding, "_gpg_keygrips", return_value={"ONE"}),
            mock.patch.object(
                _gpg_forwarding,
                "_gpg_key_is_protected",
                side_effect=[True, True],
            ),
            mock.patch.object(
                _gpg_forwarding, "_gpg_key_is_cached", return_value=False
            ),
            mock.patch.object(
                _gpg_forwarding,
                "_gpg_passphrase",
                side_effect=["first secret", "second secret"],
            ) as passphrase_mock,
            mock.patch.object(_gpg_forwarding, "_load_gpg_key") as load_mock,
        ):
            _gpg_forwarding._reload_gpg_keys([resource], interactive=False)

        self.assertEqual(
            [
                mock.call("FIRST", interactive=False),
                mock.call("SECOND", interactive=False),
            ],
            passphrase_mock.call_args_list,
        )
        self.assertEqual(
            [
                mock.call(resource, "FIRST", "first secret"),
                mock.call(resource, "SECOND", "second secret"),
            ],
            load_mock.call_args_list,
        )

    def test_reload_gpg_keys_resets_stale_sidecar_state(self) -> None:
        resource = _resources([_CredentialProtocol.GPG])[0]
        with (
            mock.patch.object(
                _gpg_forwarding,
                "resolve_gpg_secret_key_state",
                return_value=([], {"HOST"}),
            ),
            mock.patch.object(_gpg_forwarding, "_gpg_keygrips", return_value={"STALE"}),
            mock.patch.object(_gpg_forwarding, "_reset_gpg_agent") as reset_mock,
        ):
            _gpg_forwarding._reload_gpg_keys([resource], interactive=False)

        reset_mock.assert_called_once_with(resource)

    def test_reload_gpg_keys_skips_cached_protected_keys(self) -> None:
        resource = _resources([_CredentialProtocol.GPG])[0]
        with (
            mock.patch.object(
                _gpg_forwarding,
                "resolve_gpg_secret_key_state",
                return_value=(["FINGERPRINT"], {"KEY"}),
            ),
            mock.patch.object(_gpg_forwarding, "_gpg_keygrips", return_value={"KEY"}),
            mock.patch.object(
                _gpg_forwarding, "_gpg_key_is_protected", return_value=True
            ),
            mock.patch.object(_gpg_forwarding, "_gpg_key_is_cached", return_value=True),
            mock.patch.object(_gpg_forwarding, "_load_gpg_key") as load_mock,
        ):
            _gpg_forwarding._reload_gpg_keys([resource], interactive=False)

        load_mock.assert_not_called()

    def test_reload_gpg_keys_skips_an_unprotected_key(self) -> None:
        resource = _resources([_CredentialProtocol.GPG])[0]
        with (
            mock.patch.object(
                _gpg_forwarding,
                "resolve_gpg_secret_key_state",
                return_value=(["FINGERPRINT"], {"KEY"}),
            ),
            mock.patch.object(_gpg_forwarding, "_gpg_keygrips", return_value={"KEY"}),
            mock.patch.object(
                _gpg_forwarding, "_gpg_key_is_protected", return_value=False
            ),
            mock.patch.object(_gpg_forwarding, "_load_gpg_key") as load_mock,
        ):
            _gpg_forwarding._reload_gpg_keys([resource], interactive=False)

        load_mock.assert_not_called()

    def test_gpg_passphrase_uses_the_stored_keyring_secret(self) -> None:
        with mock.patch.object(
            _gpg_forwarding, "get_secret", return_value="secret"
        ) as get_mock:
            actual = _gpg_forwarding._gpg_passphrase("FINGERPRINT", interactive=False)

        self.assertEqual("secret", actual)
        get_mock.assert_called_once_with("aicage/gpg/passphrase/FINGERPRINT")

    def test_gpg_passphrase_requires_interactive_setup_for_a_missing_secret(
        self,
    ) -> None:
        with (
            mock.patch.object(
                _gpg_forwarding,
                "get_secret",
                side_effect=_gpg_forwarding.SecretNotFoundError(),
            ),
            mock.patch.object(_gpg_forwarding.sys.stdin, "isatty", return_value=False),
            self.assertRaisesRegex(RuntimeError, "Open the terminal configuration UI"),
        ):
            _gpg_forwarding._gpg_passphrase("FINGERPRINT", interactive=False)

    def test_gpg_passphrase_stores_an_interactive_secret(self) -> None:
        with (
            mock.patch.object(
                _gpg_forwarding,
                "get_secret",
                side_effect=_gpg_forwarding.SecretNotFoundError(),
            ),
            mock.patch.object(_gpg_forwarding.sys.stdin, "isatty", return_value=True),
            mock.patch.object(_gpg_forwarding, "getpass", return_value="secret"),
            mock.patch.object(_gpg_forwarding, "set_secret") as set_mock,
        ):
            self.assertEqual(
                "secret",
                _gpg_forwarding._gpg_passphrase("FINGERPRINT", interactive=True),
            )

        set_mock.assert_called_once_with("aicage/gpg/passphrase/FINGERPRINT", "secret")
