import os
from pathlib import Path
from unittest import TestCase, mock

from aicage.runtime._host_timezone import (
    _resolve_posix_timezone,
    _resolve_windows_timezone,
    resolve_host_timezone,
)


class HostTimezoneTests(TestCase):
    def test_resolve_host_timezone_uses_existing_tz_env(self) -> None:
        with mock.patch.dict(os.environ, {"TZ": "Europe/Zurich"}, clear=True):
            result = resolve_host_timezone()

        self.assertEqual("Europe/Zurich", result)

    def test_resolve_posix_timezone_prefers_timezone_file(self) -> None:
        timezone_file = mock.Mock()
        timezone_file.is_file.return_value = True
        timezone_file.read_text.return_value = "Europe/Zurich\n"
        localtime_path = mock.Mock()

        with mock.patch("aicage.runtime._host_timezone.Path", side_effect=[timezone_file, localtime_path]):
            result = _resolve_posix_timezone()

        self.assertEqual("Europe/Zurich", result)

    def test_resolve_posix_timezone_uses_localtime_symlink(self) -> None:
        timezone_file = mock.Mock()
        timezone_file.is_file.return_value = False
        localtime_path = mock.Mock()
        localtime_path.exists.return_value = True
        localtime_path.resolve.return_value = Path("/usr/share/zoneinfo/Europe/Zurich")

        with mock.patch("aicage.runtime._host_timezone.Path", side_effect=[timezone_file, localtime_path]):
            result = _resolve_posix_timezone()

        self.assertEqual("Europe/Zurich", result)

    def test_resolve_windows_timezone_uses_powershell_mapping(self) -> None:
        process = mock.Mock(
            args=["powershell"],
            returncode=0,
            stdout="Europe/Zurich\n",
            stderr="",
        )
        with mock.patch("aicage.runtime._host_timezone.subprocess.run", return_value=process):
            result = _resolve_windows_timezone()

        self.assertEqual("Europe/Zurich", result)

    def test_resolve_windows_timezone_returns_none_when_shell_missing(self) -> None:
        with mock.patch("aicage.runtime._host_timezone.subprocess.run", side_effect=OSError):
            result = _resolve_windows_timezone()

        self.assertIsNone(result)
