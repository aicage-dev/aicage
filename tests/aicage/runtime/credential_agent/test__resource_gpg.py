from unittest import TestCase, mock

from aicage.docker.errors import DockerError
from aicage.runtime.credential_agent import _resource_gpg
from aicage.runtime.credential_agent._resource_models import (
    _CredentialProtocol,
    _resources,
)


class ResourceGpgTests(TestCase):
    def test_gpg_key_is_protected_reads_the_sidecar_result(self) -> None:
        resource = _resources([_CredentialProtocol.GPG])[0]
        client = mock.Mock()
        client.api.exec_create.return_value = {"Id": "protected"}
        client.api.exec_start.return_value = b"protected\n"
        client.api.exec_inspect.return_value = {"ExitCode": 0}
        container = mock.Mock()
        with (
            mock.patch.object(_resource_gpg, "get_docker_client", return_value=client),
            mock.patch.object(_resource_gpg, "_find_container", return_value=container),
        ):
            self.assertTrue(_resource_gpg._gpg_key_is_protected(resource, "FINGERPRINT"))

        client.api.exec_create.assert_called_once_with(
            container.id,
            ["credential-agent", "gpg", "protected", "FINGERPRINT"],
        )

    def test_gpg_key_is_protected_rejects_a_failed_exec(self) -> None:
        resource = _resources([_CredentialProtocol.GPG])[0]
        client = mock.Mock()
        client.api.exec_create.return_value = {"Id": "exec-id"}
        client.api.exec_start.return_value = b"gpg: key lookup failed\n"
        client.api.exec_inspect.return_value = {"ExitCode": 1}
        with (
            mock.patch.object(_resource_gpg, "get_docker_client", return_value=client),
            mock.patch.object(_resource_gpg, "_find_container", return_value=mock.Mock()),
            self.assertRaisesRegex(DockerError, "gpg: key lookup failed"),
        ):
            _resource_gpg._gpg_key_is_protected(resource, "FINGERPRINT")

    def test_load_gpg_key_streams_passphrase_to_sidecar(self) -> None:
        resource = _resources([_CredentialProtocol.GPG])[0]
        client = mock.Mock()
        stream = mock.Mock()
        client.api.exec_create.return_value = {"Id": "exec-id"}
        client.api.exec_start.return_value = stream
        client.api.exec_inspect.return_value = {"ExitCode": 0}
        container = mock.Mock()
        with (
            mock.patch.object(_resource_gpg, "get_docker_client", return_value=client),
            mock.patch.object(_resource_gpg, "_find_container", return_value=container),
        ):
            _resource_gpg._load_gpg_key(resource, "FINGERPRINT", "secret")

        stream.sendall.assert_called_once_with(b"secret\n")
        client.api.exec_create.assert_called_once_with(
            container.id,
            ["credential-agent", "gpg", "load", "FINGERPRINT"],
            stdin=True,
        )

    def test_sidecar_container_rejects_a_missing_sidecar(self) -> None:
        resource = _resources([_CredentialProtocol.GPG])[0]
        with (
            mock.patch.object(_resource_gpg, "get_docker_client"),
            mock.patch.object(_resource_gpg, "_find_container", return_value=None),
            self.assertRaisesRegex(DockerError, "unavailable"),
        ):
            _resource_gpg._sidecar_container(mock.Mock(), resource)
