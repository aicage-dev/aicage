from unittest import TestCase, mock

from aicage.runtime.credential_agent import _sidecars
from aicage.runtime.credential_agent._resource_models import _CredentialProtocol
from aicage.runtime.credential_agent._resources import ResourceSetup


class CredentialAgentSidecarsTests(TestCase):
    def test__ensure_sidecars_resolves_image_once_for_both_protocols(self) -> None:
        reporter = mock.Mock()
        resources = [mock.Mock()]
        with (
            mock.patch(
                "aicage.runtime.credential_agent._sidecars.ensure_credential_image",
                return_value=("image:tag", "image-id"),
            ) as image_mock,
            mock.patch(
                "aicage.runtime.credential_agent._sidecars._ensure_resources",
                return_value=resources,
            ) as resources_mock,
        ):
            actual = _sidecars._ensure_sidecars(
                [_CredentialProtocol.SSH, _CredentialProtocol.GPG],
                "1000:1000",
                reporter,
            )

        self.assertEqual(resources, actual)
        image_mock.assert_called_once_with(reporter)
        resources_mock.assert_called_once_with(
            [_CredentialProtocol.SSH, _CredentialProtocol.GPG],
            "image:tag",
            "image-id",
            "1000:1000",
            ResourceSetup(),
        )

    def test__ensure_sidecars_skips_image_without_protocols(self) -> None:
        reporter = mock.Mock()
        with mock.patch(
            "aicage.runtime.credential_agent._sidecars.ensure_credential_image"
        ) as image_mock:
            actual = _sidecars._ensure_sidecars([], "1000:1000", reporter)

        self.assertEqual([], actual)
        image_mock.assert_not_called()
