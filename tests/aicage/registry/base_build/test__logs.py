from pathlib import Path
from unittest import TestCase, mock

from aicage.registry.base_build import _logs


class BaseBuildLogsTests(TestCase):
    def test_build_log_path_uses_base_dir(self) -> None:
        with (
            mock.patch("aicage.registry.base_build._logs.BASE_IMAGE_BUILD_LOG_DIR", Path("/tmp/logs")),
            mock.patch("aicage.registry.base_build._logs.timestamp", return_value="stamp"),
        ):
            build_log = _logs.build_log_path("base")
        self.assertEqual(Path("/tmp/logs") / "base-stamp.log", build_log)
