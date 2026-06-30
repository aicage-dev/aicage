from unittest import TestCase, mock

from aicage.config.base.architecture import _host_architecture, base_supports_host_architecture


class BaseArchitectureTests(TestCase):
    def test__host_architecture_normalizes_x86_64(self) -> None:
        with mock.patch("aicage.config.base.architecture.platform.machine", return_value="x86_64"):
            self.assertEqual("amd64", _host_architecture())

    def test__host_architecture_normalizes_arm64(self) -> None:
        with mock.patch("aicage.config.base.architecture.platform.machine", return_value="ARM64"):
            self.assertEqual("arm64", _host_architecture())

    def test_base_supports_host_architecture_filters_unsupported_architecture(self) -> None:
        with mock.patch("aicage.config.base.architecture.platform.machine", return_value="aarch64"):
            self.assertFalse(base_supports_host_architecture(["amd64"]))

    def test_base_supports_host_architecture_allows_unknown_host(self) -> None:
        with mock.patch("aicage.config.base.architecture.platform.machine", return_value="mips64"):
            self.assertTrue(base_supports_host_architecture(["amd64"]))
