import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from unittest import TestCase, mock

from aicage.runtime import _ssh_agent

_MODULE = "aicage.runtime._ssh_agent"


class SshAgentTests(TestCase):
    def test_resolve_ssh_key_files_includes_ssh_and_configured_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            ssh_dir = root / ".ssh"
            ssh_dir.mkdir()
            default_key = ssh_dir / "id_ed25519"
            default_key.touch()
            external_key = root / "work-key"
            external_key.touch()
            config_dir = ssh_dir / "config.d"
            config_dir.mkdir()
            included = config_dir / "work"
            included.write_text(f"IdentityFile {external_key}\n", encoding="utf-8")
            (ssh_dir / "config").write_text(
                f"Include config.d/*\nIdentityFile {default_key}\n",
                encoding="utf-8",
            )
            (ssh_dir / "known_hosts").touch()
            (ssh_dir / "id_ed25519.pub").touch()
            (external_key.with_name("work-key.pub")).touch()

            with mock.patch(f"{_MODULE}.HOST_SSH_DIR", ssh_dir):
                keys = _ssh_agent._resolve_ssh_key_files()
                support_files = _ssh_agent._resolve_ssh_support_files()

        self.assertEqual([default_key, external_key], keys)
        self.assertEqual(
            [
                ssh_dir / "config",
                included,
                ssh_dir / "known_hosts",
                ssh_dir / "id_ed25519.pub",
                external_key.with_name("work-key.pub"),
            ],
            support_files,
        )

    def test_has_ssh_support_uses_keys_without_an_agent(self) -> None:
        with mock.patch(
            f"{_MODULE}._resolve_ssh_key_files", return_value=[Path("key")]
        ):
            self.assertTrue(_ssh_agent._has_ssh_support())

    def test_has_ssh_support_uses_agent_without_keys(self) -> None:
        with (
            mock.patch(f"{_MODULE}._resolve_ssh_key_files", return_value=[]),
            mock.patch(
                f"{_MODULE}._resolve_ssh_agent_socket",
                return_value=Path("/test-tmp/agent.sock"),
            ),
        ):
            self.assertTrue(_ssh_agent._has_ssh_support())

    def test_resolve_ssh_config_files_skips_missing_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with mock.patch(f"{_MODULE}.HOST_SSH_DIR", Path(tmp_dir) / ".ssh"):
                self.assertEqual([], _ssh_agent._resolve_ssh_config_files())

    def test_configured_private_key_files_skips_dynamic_and_missing_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            private_key = Path(tmp_dir) / "key"
            private_key.touch()
            config = Path(tmp_dir) / "config"
            config.write_text(
                f"IdentityFile {private_key}.pub\n"
                "IdentityFile ~/.ssh/%h\n"
                "IdentityFile /missing\n",
                encoding="utf-8",
            )
            with mock.patch(
                f"{_MODULE}._resolve_ssh_config_files", return_value=[config]
            ):
                paths = _ssh_agent._configured_private_key_files()

        self.assertEqual([private_key], paths)

    def test_forwarding_mounts_socket_and_public_support_files(self) -> None:
        socket = Path("/test-tmp/agent.sock")
        config = Path("/test-tmp/.ssh/config")
        public_key = Path("/test-tmp/.ssh/id_ed25519.pub")
        connection = _ssh_agent._AgentConnection(socket, {}, False)
        with (
            mock.patch(f"{_MODULE}._connect_agent", return_value=connection),
            mock.patch(f"{_MODULE}._resolve_ssh_key_files", return_value=[Path("key")]),
            mock.patch(
                f"{_MODULE}._resolve_ssh_support_files",
                return_value=[config, public_key],
            ),
            mock.patch(f"{_MODULE}._add_keys", return_value=[Path("key")]),
            mock.patch(f"{_MODULE}._remove_keys") as remove_keys_mock,
        ):
            with _ssh_agent.forwarding(True) as (mounts, env):
                self.assertEqual(socket, mounts[0].host_path)
                self.assertEqual(
                    PurePosixPath("/run/aicage-ssh-agent.sock"),
                    mounts[0].container_path,
                )
                self.assertTrue(mounts[1].read_only)
                self.assertEqual("SSH_AUTH_SOCK", env[0].name)

        remove_keys_mock.assert_called_once_with({}, [Path("key")])

    def test_forwarding_stops_temporary_agent(self) -> None:
        connection = _ssh_agent._AgentConnection(Path("/test-tmp/agent.sock"), {}, True)
        with (
            mock.patch(f"{_MODULE}._connect_agent", return_value=connection),
            mock.patch(f"{_MODULE}._resolve_ssh_key_files", return_value=[]),
            mock.patch(f"{_MODULE}._resolve_ssh_support_files", return_value=[]),
            mock.patch(f"{_MODULE}._stop_agent") as stop_agent_mock,
        ):
            with _ssh_agent.forwarding(True):
                pass

        stop_agent_mock.assert_called_once_with({})

    def test_forwarding_skips_disabled_or_unavailable_agent(self) -> None:
        with _ssh_agent.forwarding(False) as resolved:
            self.assertEqual(([], []), resolved)

        with mock.patch(f"{_MODULE}._connect_agent", return_value=None):
            with _ssh_agent.forwarding(True) as resolved:
                self.assertEqual(([], []), resolved)

    def test_connect_agent_uses_reachable_socket(self) -> None:
        socket = Path("/test-tmp/agent.sock")
        with (
            mock.patch(f"{_MODULE}._resolve_ssh_agent_socket", return_value=socket),
            mock.patch(f"{_MODULE}._agent_is_reachable", return_value=True),
        ):
            connection = _ssh_agent._connect_agent()

        self.assertEqual(socket, connection.socket if connection else None)
        self.assertFalse(connection.temporary if connection else True)

    def test_connect_agent_falls_back_to_temporary_unix_agent(self) -> None:
        connection = _ssh_agent._AgentConnection(Path("/test-tmp/new.sock"), {}, True)
        with (
            mock.patch(
                f"{_MODULE}._resolve_ssh_agent_socket", return_value=Path("old.sock")
            ),
            mock.patch(f"{_MODULE}._agent_is_reachable", return_value=False),
            mock.patch(f"{_MODULE}._start_unix_agent", return_value=connection),
            mock.patch(f"{_MODULE}.os.name", "posix"),
        ):
            self.assertIs(connection, _ssh_agent._connect_agent())

    def test_start_unix_agent_handles_failure_and_parses_socket(self) -> None:
        failed = subprocess.CompletedProcess([], 1, stdout="", stderr="")
        started = subprocess.CompletedProcess(
            [],
            0,
            stdout="SSH_AUTH_SOCK=/test-tmp/agent.sock; export SSH_AUTH_SOCK;\n",
            stderr="",
        )
        with mock.patch(f"{_MODULE}.subprocess.run", side_effect=[failed, started]):
            self.assertIsNone(_ssh_agent._start_unix_agent())
            connection = _ssh_agent._start_unix_agent()

        self.assertEqual(
            Path("/test-tmp/agent.sock"), connection.socket if connection else None
        )

    def test_start_windows_agent_returns_named_pipe_after_starting_service(
        self,
    ) -> None:
        socket = Path(r"\\.\pipe\openssh-ssh-agent")
        with (
            mock.patch(f"{_MODULE}.subprocess.run") as run_mock,
            mock.patch(f"{_MODULE}._resolve_ssh_agent_socket", return_value=socket),
        ):
            connection = _ssh_agent._start_windows_agent()

        self.assertEqual(socket, connection.socket if connection else None)
        self.assertFalse(connection.temporary if connection else True)
        run_mock.assert_called_once()

    def test_add_keys_tracks_only_successful_additions_and_remove_keys(self) -> None:
        successful: subprocess.CompletedProcess[bytes] = subprocess.CompletedProcess(
            [], 0
        )
        failed: subprocess.CompletedProcess[bytes] = subprocess.CompletedProcess([], 1)
        first = Path("/test-tmp/first")
        second = Path("/test-tmp/second")
        with mock.patch(f"{_MODULE}.subprocess.run", side_effect=[successful, failed]):
            added = _ssh_agent._add_keys({}, [first, second])

        self.assertEqual([first], added)
        with mock.patch(f"{_MODULE}.subprocess.run") as run_mock:
            _ssh_agent._remove_keys({}, added)

        run_mock.assert_called_once()
