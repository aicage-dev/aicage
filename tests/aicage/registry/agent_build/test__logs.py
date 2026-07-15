from pathlib import Path
from unittest import TestCase, mock

from aicage.registry.agent_build import _logs


class AgentBuildLogsTests(TestCase):
    def test_build_log_path_uses_timestamp(self) -> None:
        with mock.patch(
            "aicage.registry.agent_build._logs.timestamp", return_value="stamp"
        ):
            build_log = _logs.build_log_path("claude", "ubuntu")

        self.assertTrue(str(build_log).endswith("claude-ubuntu-stamp.log"))

    def test_build_log_path_uses_base_dir(self) -> None:
        with (
            mock.patch(
                "aicage.registry.agent_build._logs.IMAGE_BUILD_LOG_DIR",
                Path("/test-tmp/logs"),
            ),
            mock.patch(
                "aicage.registry.agent_build._logs.timestamp", return_value="stamp"
            ),
        ):
            build_log = _logs.build_log_path("claude", "ubuntu")
        self.assertEqual(Path("/test-tmp/logs") / "claude-ubuntu-stamp.log", build_log)
