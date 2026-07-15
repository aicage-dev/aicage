from unittest import TestCase

from aicage.runtime.menu.textual import _ids


class IdsTests(TestCase):
    def test_built_in_selection_key_formats_value(self) -> None:
        self.assertEqual(
            "builtin:git_support:ssh", _ids.built_in_selection_key("git_support", "ssh")
        )

    def test_built_in_identity_formats_value(self) -> None:
        self.assertEqual(
            "git_support:ssh", _ids.built_in_identity("git_support", "ssh")
        )

    def test_custom_share_selection_key_formats_value(self) -> None:
        self.assertEqual(
            "custom:/test-tmp/logs", _ids.custom_share_selection_key("/test-tmp/logs")
        )

    def test_docker_selection_key_formats_value(self) -> None:
        self.assertEqual("docker:socket", _ids.docker_selection_key("socket"))
