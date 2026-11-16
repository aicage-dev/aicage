from unittest import TestCase, mock

from aicage.runtime.credential_agent import _sidecars
from aicage.runtime.credential_agent._resource_models import (
    _CredentialProtocol,
    _ImageSpec,
)
from aicage.runtime.credential_agent._resources import ResourceSetup


class CredentialAgentSidecarsTests(TestCase):
    def test__ensure_sidecars_uses_the_prepared_image_for_both_protocols(self) -> None:
        resources = [mock.Mock()]
        image = _ImageSpec("image:tag", "image-id", "1000:1000")
        with mock.patch(
            "aicage.runtime.credential_agent._sidecars._ensure_resources",
            return_value=resources,
        ) as resources_mock:
            actual = _sidecars._ensure_sidecars(
                [_CredentialProtocol.SSH, _CredentialProtocol.GPG],
                image,
            )

        self.assertEqual(resources, actual)
        resources_mock.assert_called_once_with(
            [_CredentialProtocol.SSH, _CredentialProtocol.GPG],
            "image:tag",
            "image-id",
            "1000:1000",
            ResourceSetup(),
        )

    def test__ensure_sidecars_skips_resources_without_protocols(self) -> None:
        actual = _sidecars._ensure_sidecars([], _ImageSpec("image", "id", "1000"))

        self.assertEqual([], actual)
