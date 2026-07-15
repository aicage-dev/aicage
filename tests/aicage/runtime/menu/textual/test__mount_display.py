from unittest import TestCase

from aicage.config.project_config import MOUNT_GITCONFIG_KEY
from aicage.runtime.menu.textual import _mount_display
from aicage.runtime.menu.textual._models import BuiltInShareValue, CustomShareValue


class MountDisplayTests(TestCase):
    def test_git_support_label_returns_known_label(self) -> None:
        value = _mount_display.git_support_label(MOUNT_GITCONFIG_KEY)

        self.assertEqual("Git config", value)

    def test_extension_label_returns_prefixed_label(self) -> None:
        value = _mount_display.extension_label("gh")

        self.assertEqual("Extension gh", value)

    def test_overview_mount_list_items_returns_built_in_and_custom_items(self) -> None:
        values = _mount_display.overview_mount_list_items(
            [
                BuiltInShareValue(
                    "git_support", "ssh", "SSH", "/test-tmp/.ssh", None, True
                )
            ],
            [CustomShareValue("/test-tmp/logs:ro"), CustomShareValue("/test-tmp/data")],
        )

        self.assertEqual("SSH", values[0].prefix)
        self.assertEqual("/test-tmp/.ssh", values[0].path)
        self.assertEqual("builtin:git_support:ssh", values[0].selection_key)
        self.assertTrue(values[0].enabled)
        self.assertEqual("Read-only", values[1].prefix)
        self.assertEqual("/test-tmp/logs", values[1].path)
        self.assertEqual("custom:/test-tmp/logs:ro", values[1].selection_key)
        self.assertEqual(None, values[2].prefix)
        self.assertEqual("/test-tmp/data", values[2].path)
        self.assertEqual("custom:/test-tmp/data", values[2].selection_key)

    def test_confirm_mount_list_items_returns_confirm_items(self) -> None:
        values = _mount_display.confirm_mount_list_items(
            [
                BuiltInShareValue(
                    "extension",
                    "gh",
                    "Extension gh",
                    "/test-tmp/gh:ro",
                    None,
                    False,
                    "gh:/test-tmp/gh:ro",
                )
            ]
        )

        self.assertEqual("Extension gh", values[0].prefix)
        self.assertEqual("Read-only: /test-tmp/gh", values[0].path)
        self.assertEqual(
            "builtin:extension:gh:/test-tmp/gh:ro", values[0].selection_key
        )
        self.assertFalse(values[0].enabled)

    def test_mount_selection_rows_aligns_prefixes(self) -> None:
        rows = _mount_display.mount_selection_rows(
            _mount_display.overview_mount_list_items(
                [
                    BuiltInShareValue(
                        "git_support", "ssh", "SSH", "/test-tmp/.ssh", None, True
                    )
                ],
                [CustomShareValue("/test-tmp/data")],
            )
        )

        self.assertEqual(
            [
                ("SSH: /test-tmp/.ssh", "builtin:git_support:ssh", True),
                ("   : /test-tmp/data", "custom:/test-tmp/data", True),
            ],
            rows,
        )
