from unittest import TestCase

from aicage.runtime.menu.textual import _mount_value


class MountValueTests(TestCase):
    def test_split_mount_value_detects_read_only_suffix(self) -> None:
        value = _mount_value.split_mount_value("/tmp/logs:ro")

        self.assertEqual(("/tmp/logs", True), value)

    def test_compose_mount_value_appends_read_only_suffix(self) -> None:
        value = _mount_value.compose_mount_value("/tmp/logs", True)

        self.assertEqual("/tmp/logs:ro", value)

    def test_display_mount_value_prefixes_read_only(self) -> None:
        value = _mount_value.display_mount_value("/tmp/logs:ro")

        self.assertEqual("Read-only: /tmp/logs", value)
