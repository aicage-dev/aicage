from unittest import TestCase, mock

from aicage.registry import ensure_util_image


class EnsureUtilImageTests(TestCase):
    def test_ensure_util_image_pulls_a_missing_image(self) -> None:
        with (
            mock.patch.object(
                ensure_util_image, "get_local_repo_digest_for_repo", return_value=None
            ),
            mock.patch.object(ensure_util_image, "resolve_verified_digest"),
            mock.patch.object(ensure_util_image, "run_pull") as pull_mock,
            mock.patch.object(ensure_util_image, "cleanup_old_digest") as cleanup_mock,
        ):
            ensure_util_image.ensure_util_image("example/image:tag", mock.Mock())

        pull_mock.assert_called_once()
        cleanup_mock.assert_called_once()
