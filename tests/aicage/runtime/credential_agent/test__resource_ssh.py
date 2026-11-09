from pathlib import PurePosixPath
from unittest import TestCase, mock

from aicage.docker.errors import DockerError
from aicage.runtime.credential_agent import _resource_ssh
from aicage.runtime.credential_agent._resource_models import (
    _CredentialProtocol,
    _resources,
)


class ResourceSshTests(TestCase):
    def test_close_exec_stream_closes_retained_response_before_stream(self) -> None:
        stream = mock.Mock()
        response = mock.Mock()
        stream.attach_mock(response, "_response")

        _resource_ssh._close_exec_stream(stream)

        self.assertEqual(
            [mock.call._response.close(), mock.call.close()], stream.mock_calls
        )

    def test_write_exec_input_uses_socket_io_socket_when_stream_is_not_writable(
        self,
    ) -> None:
        socket = mock.Mock()
        stream = mock.Mock(spec=["_sock", "writable"])
        stream._sock = socket
        stream.writable.return_value = False

        _resource_ssh._write_exec_input(stream, b"secret\n")

        socket.sendall.assert_called_once_with(b"secret\n")

    def test_write_exec_input_uses_socket_io_write_when_sendall_is_unavailable(
        self,
    ) -> None:
        stream = mock.Mock(spec=["write"])
        stream.write.return_value = 7

        _resource_ssh._write_exec_input(stream, b"secret\n")

        stream.write.assert_called_once_with(b"secret\n")

    def test_load_ssh_key_streams_passphrase_to_sidecar(self) -> None:
        resource = _resources([_CredentialProtocol.SSH])[0]
        stream = mock.Mock()
        client = mock.Mock()
        client.api.exec_create.return_value = {"Id": "exec-id"}
        client.api.exec_start.return_value = stream
        client.api.exec_inspect.return_value = {"ExitCode": 0}
        container = mock.Mock()
        with (
            mock.patch.object(_resource_ssh, "get_docker_client", return_value=client),
            mock.patch.object(_resource_ssh, "_find_container", return_value=container),
        ):
            _resource_ssh._load_ssh_key(
                resource, PurePosixPath("/credential/ssh/id_ed25519"), "secret"
            )

        stream.sendall.assert_called_once_with(b"secret\n")
        stream.close.assert_called_once()
        client.api.exec_create.assert_called_once_with(
            container.id,
            ["credential-agent", "ssh", "load", "/credential/ssh/id_ed25519"],
            stdin=True,
        )

    def test_load_ssh_key_rejects_missing_sidecar(self) -> None:
        resource = _resources([_CredentialProtocol.SSH])[0]
        with (
            mock.patch.object(_resource_ssh, "get_docker_client"),
            mock.patch.object(_resource_ssh, "_find_container", return_value=None),
            self.assertRaisesRegex(DockerError, "unavailable"),
        ):
            _resource_ssh._load_ssh_key(
                resource, PurePosixPath("/credential/ssh/id_ed25519"), ""
            )

    def test_load_ssh_key_rejects_a_failed_exec(self) -> None:
        resource = _resources([_CredentialProtocol.SSH])[0]
        client = mock.Mock()
        client.api.exec_create.return_value = {"Id": "exec-id"}
        stream = mock.Mock()
        client.api.exec_start.return_value = stream
        client.api.exec_inspect.return_value = {"ExitCode": 1}
        with (
            mock.patch.object(_resource_ssh, "get_docker_client", return_value=client),
            mock.patch.object(
                _resource_ssh, "_find_container", return_value=mock.Mock()
            ),
            self.assertRaisesRegex(DockerError, "Failed to load"),
        ):
            _resource_ssh._load_ssh_key(
                resource, PurePosixPath("/credential/ssh/id_ed25519"), ""
            )

    def test_load_ssh_key_waits_for_remote_exec_completion(self) -> None:
        resource = _resources([_CredentialProtocol.SSH])[0]
        stream = mock.Mock()
        client = mock.Mock()
        client.api.exec_create.return_value = {"Id": "exec-id"}
        client.api.exec_start.return_value = stream
        client.api.exec_inspect.side_effect = [
            {"Running": True, "ExitCode": None},
            {"Running": False, "ExitCode": 0},
        ]
        with (
            mock.patch.object(_resource_ssh, "get_docker_client", return_value=client),
            mock.patch.object(
                _resource_ssh, "_find_container", return_value=mock.Mock()
            ),
            mock.patch.object(_resource_ssh.time, "sleep"),
        ):
            _resource_ssh._load_ssh_key(
                resource, PurePosixPath("/credential/ssh/id_ed25519"), ""
            )

        self.assertEqual(2, client.api.exec_inspect.call_count)

    def test_load_ssh_key_does_not_read_exec_output(self) -> None:
        resource = _resources([_CredentialProtocol.SSH])[0]
        stream = mock.Mock()
        client = mock.Mock()
        client.api.exec_create.return_value = {"Id": "load-id"}
        client.api.exec_start.return_value = stream
        client.api.exec_inspect.return_value = {"ExitCode": 1}
        with (
            mock.patch.object(_resource_ssh, "get_docker_client", return_value=client),
            mock.patch.object(
                _resource_ssh, "_find_container", return_value=mock.Mock()
            ),
            self.assertRaisesRegex(DockerError, "Failed to load"),
        ):
            _resource_ssh._load_ssh_key(
                resource, PurePosixPath("/credential/ssh/id_ed25519"), ""
            )

        stream.recv.assert_not_called()

    def test_load_ssh_key_translates_docker_exec_errors(self) -> None:
        resource = _resources([_CredentialProtocol.SSH])[0]
        client = mock.Mock()
        client.api.exec_create.side_effect = _resource_ssh.DockerException("failed")
        with (
            mock.patch.object(_resource_ssh, "get_docker_client", return_value=client),
            mock.patch.object(
                _resource_ssh, "_find_container", return_value=mock.Mock()
            ),
            self.assertRaisesRegex(DockerError, "Failed to load"),
        ):
            _resource_ssh._load_ssh_key(
                resource, PurePosixPath("/credential/ssh/id_ed25519"), ""
            )
