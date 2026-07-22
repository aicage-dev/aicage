from unittest import TestCase

from aicage.config.image_refs import (
    default_extended_image_ref,
    extended_image_name,
    local_image_ref,
)


class ImageRefsTests(TestCase):
    def test_local_image_ref_formats_tag(self) -> None:
        self.assertEqual(
            "aicage:agent-ubuntu", local_image_ref("aicage", "Agent", "Ubuntu")
        )
        self.assertEqual(
            "aicage:agent-sub-base", local_image_ref("aicage", "agent/sub", "base")
        )

    def test_default_extended_image_ref_sorts_extensions(self) -> None:
        self.assertEqual(
            "aicage-extended:codex-ubuntu-alpha-zeta",
            default_extended_image_ref("codex", "ubuntu", ["zeta", "alpha"]),
        )

    def test_extended_image_name_extracts_tag(self) -> None:
        self.assertEqual("tag", extended_image_name("repo:tag"))
        self.assertEqual("latest", extended_image_name("registry.io/repo:latest"))

    def test_extended_image_name_returns_ref_without_tag(self) -> None:
        self.assertEqual("repo", extended_image_name("repo"))
