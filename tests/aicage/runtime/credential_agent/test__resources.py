from contextlib import AbstractContextManager
from pathlib import Path
from unittest import TestCase, mock

import portalocker
from docker.errors import DockerException, NotFound

from aicage.docker.errors import DockerError
from aicage.runtime.credential_agent import _resources
from aicage.runtime.credential_agent._resource_lifecycle import _resource_lock
from aicage.runtime.credential_agent._resource_models import (
    _CredentialProtocol,
)
from aicage.runtime.credential_agent._resource_models import (
    _resources as _resource_definitions,
)


class CredentialAgentResourcesTests(TestCase):
    def setUp(self) -> None:
        self._ssh = _CredentialProtocol.SSH
        self._resource = _resource_definitions([self._ssh])[0]
        self._labels = {
            "org.aicage.resource": "credential-agent",
            "org.aicage.credential-agent.protocol": "ssh",
            "org.aicage.credential-agent.version": "1",
            "org.aicage.credential-agent.image-id": "image-id",
        }

    def test__ensure_resources_creates_missing_volume_and_sidecar(self) -> None:
        client = mock.Mock()
        volume = mock.Mock(name=self._resource.volume_name, labels=self._labels)
        container = self._container(status="running")
        client.volumes.get.side_effect = NotFound("missing")
        client.volumes.create.return_value = volume
        client.containers.get.side_effect = NotFound("missing")
        client.containers.run.side_effect = [None, container, None]

        with self._client(client):
            resources = _resources._ensure_resources(
                [self._ssh], "image:tag", "image-id", "1000:1000"
            )

        self.assertEqual([self._resource], resources)
        client.volumes.create.assert_called_once_with(
            name=self._resource.volume_name,
            labels={
                "org.aicage.resource": "credential-agent",
                "org.aicage.credential-agent.protocol": "ssh",
                "org.aicage.credential-agent.version": "1",
            },
        )
        self.assertEqual(3, client.containers.run.call_count)

    def test__ensure_resources_restarts_stopped_owned_sidecar(self) -> None:
        client = mock.Mock()
        volume = mock.Mock(name=self._resource.volume_name, labels=self._labels)
        container = self._container(status="exited")
        client.volumes.get.return_value = volume
        client.containers.get.return_value = container

        with self._client(client):
            _resources._ensure_resources(
                [self._ssh], "image:tag", "image-id", "1000:1000"
            )

        container.start.assert_called_once()
        container.remove.assert_not_called()
        self.assertEqual(2, client.containers.run.call_count)

    def test__ensure_resources_replaces_unhealthy_or_obsolete_sidecar(self) -> None:
        cases: tuple[tuple[dict[str, str], dict[str, object]], ...] = (
            (self._labels, {"Status": "running", "Health": {"Status": "unhealthy"}}),
            (
                {**self._labels, "org.aicage.credential-agent.image-id": "old"},
                {"Status": "running"},
            ),
        )
        for labels, state in cases:
            with self.subTest(labels=labels, state=state):
                client = mock.Mock()
                volume = mock.Mock(name=self._resource.volume_name, labels=self._labels)
                container = self._container(labels=labels, state=state)
                client.volumes.get.return_value = volume
                client.containers.get.return_value = container
                client.containers.run.side_effect = [
                    None,
                    self._container(status="running"),
                    None,
                ]

                with self._client(client):
                    _resources._ensure_resources(
                        [self._ssh], "image:tag", "image-id", "1000:1000"
                    )

                container.remove.assert_called_once_with(force=True)
                client.volumes.create.assert_not_called()

    def test__ensure_resources_rejects_unowned_volume(self) -> None:
        client = mock.Mock()
        client.volumes.get.return_value = mock.Mock(
            name=self._resource.volume_name,
            labels={},
        )

        with self._client(client), self.assertRaisesRegex(DockerError, "not owned"):
            _resources._ensure_resources(
                [self._ssh], "image:tag", "image-id", "1000:1000"
            )

    def test__ensure_resources_rejects_unowned_sidecar(self) -> None:
        client = mock.Mock()
        volume = mock.Mock(name=self._resource.volume_name, labels=self._labels)
        client.volumes.get.return_value = volume
        client.containers.get.return_value = self._container(labels={})

        with self._client(client), self.assertRaisesRegex(DockerError, "not owned"):
            _resources._ensure_resources(
                [self._ssh], "image:tag", "image-id", "1000:1000"
            )

    def test__ensure_resources_replaces_stale_resource_version(self) -> None:
        client = mock.Mock()
        volume = mock.Mock(name=self._resource.volume_name, labels=self._labels)
        labels = {**self._labels, "org.aicage.credential-agent.version": "old"}
        container = self._container(labels=labels, status="running")
        client.volumes.get.return_value = volume
        client.containers.get.return_value = container
        client.containers.run.side_effect = [
            None,
            self._container(status="running"),
            None,
        ]

        with self._client(client):
            _resources._ensure_resources(
                [self._ssh], "image:tag", "image-id", "1000:1000"
            )

        container.remove.assert_called_once_with(force=True)

    def test__ensure_resources_mounts_credentials_only_in_sidecar(self) -> None:
        client = mock.Mock()
        volume = mock.Mock(name=self._resource.volume_name, labels=self._labels)
        credentials = Path("/test-tmp/.ssh")
        client.volumes.get.return_value = volume
        client.containers.get.side_effect = NotFound("missing")
        client.containers.run.side_effect = [
            None,
            self._container(status="running"),
            None,
        ]

        with (
            self._client(client),
            mock.patch.object(_resources, "HOST_SSH_DIR", credentials),
            mock.patch.object(Path, "is_dir", return_value=True),
        ):
            _resources._ensure_resources(
                [self._ssh],
                "image:tag",
                "image-id",
                "1000:1000",
            )

        sidecar_call = client.containers.run.call_args_list[1]
        self.assertEqual(
            {
                volume.name: {
                    "bind": "/run/credential-agent",
                    "mode": "rw",
                },
                str(credentials): {"bind": "/credential/ssh", "mode": "ro"},
            },
            sidecar_call.kwargs["volumes"],
        )

    def test__ensure_resources_reports_readiness_failure(self) -> None:
        client = mock.Mock()
        volume = mock.Mock(name=self._resource.volume_name, labels=self._labels)
        client.volumes.get.return_value = volume
        client.containers.get.side_effect = NotFound("missing")
        client.containers.run.side_effect = [
            None,
            self._container(status="running"),
            DockerException("not ready"),
        ]

        with (
            self._client(client),
            self.assertRaisesRegex(DockerError, "did not become ready"),
        ):
            _resources._ensure_resources(
                [self._ssh], "image:tag", "image-id", "1000:1000"
            )

    def test_resource_lock_translates_contention_error(self) -> None:
        with (
            mock.patch(
                "aicage.runtime.credential_agent._resource_lifecycle.portalocker.Lock",
                side_effect=portalocker.exceptions.LockException,
            ),
            self.assertRaisesRegex(DockerError, "Failed to lock"),
        ):
            with _resource_lock():
                pass

    def test__resources_deduplicates_protocols(self) -> None:
        resources = _resource_definitions(
            [_CredentialProtocol.SSH, _CredentialProtocol.SSH]
        )

        self.assertEqual(1, len(resources))

    def _client(self, client: mock.Mock) -> AbstractContextManager[object]:
        return mock.patch(
            "aicage.runtime.credential_agent._resources.get_docker_client",
            return_value=client,
        )

    def _container(
        self,
        *,
        status: str | None = None,
        labels: dict[str, str] | None = None,
        state: dict[str, object] | None = None,
    ) -> mock.Mock:
        container = mock.Mock(labels=self._labels if labels is None else labels)
        container.attrs = {"State": state or {"Status": status}}
        return container
