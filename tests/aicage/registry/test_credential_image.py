from unittest import TestCase, mock

from aicage import constants
from aicage.registry import credential_image

_CREDENTIAL_AGENT_REPOSITORY = (
    f"{constants.IMAGE_REGISTRY}/{constants.IMAGE_UTIL_REPOSITORY}"
)


class CredentialImageTests(TestCase):
    def test_ensure_credential_image_pulls_missing_image(self) -> None:
        reporter = mock.Mock()
        with (
            mock.patch(
                "aicage.registry.credential_image.get_local_repo_digest_for_repo",
                return_value=None,
            ),
            mock.patch(
                "aicage.registry.credential_image.resolve_verified_digest"
            ) as verify_mock,
            mock.patch("aicage.registry.credential_image.run_pull") as pull_mock,
            mock.patch(
                "aicage.registry.credential_image.cleanup_old_digest"
            ) as cleanup_mock,
            mock.patch(
                "aicage.registry.credential_image.get_local_image_id",
                return_value="image-id",
            ),
        ):
            image = credential_image.ensure_credential_image(reporter)

        self.assertEqual((constants.CREDENTIAL_AGENT_IMAGE, "image-id"), image)
        verify_mock.assert_called_once_with(
            constants.CREDENTIAL_AGENT_IMAGE, reporter=reporter
        )
        pull_mock.assert_called_once()
        cleanup_mock.assert_called_once_with(
            _CREDENTIAL_AGENT_REPOSITORY,
            None,
            constants.CREDENTIAL_AGENT_IMAGE,
        )

    def test_ensure_credential_image_skips_current_image(self) -> None:
        reporter = mock.Mock()
        with (
            mock.patch(
                "aicage.registry.credential_image.get_local_repo_digest_for_repo",
                return_value="sha256:current",
            ),
            mock.patch(
                "aicage.registry.credential_image.get_remote_digest",
                return_value="sha256:current",
            ),
            mock.patch("aicage.registry.credential_image.run_pull") as pull_mock,
            mock.patch(
                "aicage.registry.credential_image.get_local_image_id",
                return_value="image-id",
            ),
        ):
            credential_image.ensure_credential_image(reporter)

        pull_mock.assert_not_called()

    def test_ensure_credential_image_pulls_new_digest_once(self) -> None:
        reporter = mock.Mock()
        with (
            mock.patch(
                "aicage.registry.credential_image.get_local_repo_digest_for_repo",
                return_value="sha256:old",
            ),
            mock.patch(
                "aicage.registry.credential_image.get_remote_digest",
                return_value="sha256:new",
            ),
            mock.patch(
                "aicage.registry.credential_image.resolve_verified_digest"
            ) as verify_mock,
            mock.patch("aicage.registry.credential_image.run_pull") as pull_mock,
            mock.patch(
                "aicage.registry.credential_image.cleanup_old_digest"
            ) as cleanup_mock,
            mock.patch(
                "aicage.registry.credential_image.get_local_image_id",
                return_value="image-id",
            ),
        ):
            credential_image.ensure_credential_image(reporter)

        verify_mock.assert_called_once_with(
            constants.CREDENTIAL_AGENT_IMAGE, reporter=reporter
        )
        pull_mock.assert_called_once()
        cleanup_mock.assert_called_once_with(
            _CREDENTIAL_AGENT_REPOSITORY,
            "sha256:old",
            constants.CREDENTIAL_AGENT_IMAGE,
        )
