from unittest import TestCase

from aicage.config._base_exclude import is_base_excluded, normalize_exclude


class BaseExcludeTests(TestCase):
    def test_is_base_excluded_matches_by_name(self) -> None:
        self.assertTrue(
            is_base_excluded(
                base_name="Ubuntu",
                base_distro="Ubuntu",
                base_exclude={"ubuntu"},
                base_distro_exclude=set(),
            )
        )

    def test_is_base_excluded_matches_by_distro(self) -> None:
        self.assertTrue(
            is_base_excluded(
                base_name="debian",
                base_distro="Ubuntu",
                base_exclude=set(),
                base_distro_exclude={"ubuntu"},
            )
        )

    def test_is_base_excluded_returns_false_when_not_excluded(self) -> None:
        self.assertFalse(
            is_base_excluded(
                base_name="debian",
                base_distro="Debian",
                base_exclude={"ubuntu"},
                base_distro_exclude={"alpine"},
            )
        )

    def test_normalize_exclude_returns_empty_for_empty_values(self) -> None:
        self.assertEqual(set(), normalize_exclude([]))

    def test_normalize_exclude_normalizes_to_lowercase(self) -> None:
        self.assertEqual({"ubuntu", "alpine"}, normalize_exclude(["Ubuntu", "ALPINE"]))
