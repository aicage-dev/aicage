from pathlib import PurePosixPath
from unittest import TestCase, mock

from aicage.docker.errors import DockerError
from aicage.runtime.credential_agent import _resource_ssh
from aicage.runtime.credential_agent._resource_models import (
    _CredentialProtocol,
    _resources,
)


class ResourceSshTests(TestCase):
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
        client.api.exec_start.return_value = mock.Mock()
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
