from unittest import TestCase

from aicage.docker.refs import repository_from_image_ref


class RepositoryFromImageRefTests(TestCase):
    def test_repository_from_image_ref_strips_tag(self) -> None:
        self.assertEqual(
            "ghcr.io/aicage/aicage",
            repository_from_image_ref("ghcr.io/aicage/aicage:codex-ubuntu"),
        )

    def test_repository_from_image_ref_strips_digest(self) -> None:
        self.assertEqual(
            "ghcr.io/aicage/aicage",
            repository_from_image_ref("ghcr.io/aicage/aicage@sha256:deadbeef"),
        )

    def test_repository_from_image_ref_handles_local_repo(self) -> None:
        self.assertEqual(
            "aicage",
            repository_from_image_ref("aicage:claude-ubuntu"),
        )
