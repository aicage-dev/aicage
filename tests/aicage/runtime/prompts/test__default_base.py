from unittest import TestCase, mock

from aicage.runtime.prompts import _default_base


class PromptDefaultBaseTests(TestCase):
    def test_resolve_default_base_uses_id_like_matches(self) -> None:
        with (
            mock.patch("aicage.runtime.prompts._default_base.sys.platform", "linux"),
            mock.patch(
                "aicage.runtime.prompts._default_base._read_os_release",
                return_value={"id": "nobara", "id_like": "rhel centos fedora"},
            ),
        ):
            default_base = _default_base.resolve_default_base(["ubuntu", "fedora"])
        self.assertEqual("fedora", default_base)

    def test_resolve_default_base_prefers_id_before_id_like(self) -> None:
        with (
            mock.patch("aicage.runtime.prompts._default_base.sys.platform", "linux"),
            mock.patch(
                "aicage.runtime.prompts._default_base._read_os_release",
                return_value={"id": "debian", "id_like": "ubuntu debian"},
            ),
        ):
            default_base = _default_base.resolve_default_base(["debian", "ubuntu"])
        self.assertEqual("debian", default_base)

    def test_resolve_default_base_supports_custom_base_names(self) -> None:
        with (
            mock.patch("aicage.runtime.prompts._default_base.sys.platform", "linux"),
            mock.patch(
                "aicage.runtime.prompts._default_base._read_os_release",
                return_value={"id": "gentoo", "id_like": ""},
            ),
        ):
            default_base = _default_base.resolve_default_base(["ubuntu", "gentoo"])
        self.assertEqual("gentoo", default_base)

    def test_resolve_default_base_uses_fallback_when_no_match(self) -> None:
        with (
            mock.patch("aicage.runtime.prompts._default_base.sys.platform", "linux"),
            mock.patch(
                "aicage.runtime.prompts._default_base._read_os_release",
                return_value={"id": "arch", "id_like": ""},
            ),
        ):
            default_base = _default_base.resolve_default_base(["alpine", "fedora"])
        self.assertEqual("alpine", default_base)

    def test_resolve_default_base_uses_ubuntu_on_non_linux(self) -> None:
        with mock.patch("aicage.runtime.prompts._default_base.sys.platform", "win32"):
            default_base = _default_base.resolve_default_base(["fedora", "ubuntu"])
        self.assertEqual("ubuntu", default_base)
