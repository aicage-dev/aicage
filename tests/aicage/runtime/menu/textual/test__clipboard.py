import subprocess
from unittest import TestCase, mock

from aicage.runtime.menu.textual import _clipboard


class ClipboardTests(TestCase):
    def test_copy_to_clipboard_uses_fallback_when_system_copy_unavailable(self) -> None:
        fallback = mock.Mock()

        with mock.patch.object(_clipboard, "copy_to_system_clipboard", return_value=False):
            _clipboard.copy_to_clipboard("echo hi", fallback)

        fallback.assert_called_once_with("echo hi")

    def test_copy_to_clipboard_skips_fallback_when_system_copy_succeeds(self) -> None:
        fallback = mock.Mock()

        with mock.patch.object(_clipboard, "copy_to_system_clipboard", return_value=True):
            _clipboard.copy_to_clipboard("echo hi", fallback)

        fallback.assert_not_called()

    def test_copy_to_system_clipboard_returns_true_when_process_stays_alive(self) -> None:
        process = mock.Mock()
        process.stdin = mock.Mock()
        process.wait.side_effect = subprocess.TimeoutExpired(cmd="xclip", timeout=0.2)

        with (
            mock.patch.object(_clipboard, "clipboard_command", return_value=["xclip"]),
            mock.patch("aicage.runtime.menu.textual._clipboard.subprocess.Popen", return_value=process),
        ):
            copied = _clipboard.copy_to_system_clipboard("echo hi")

        self.assertTrue(copied)
        process.stdin.write.assert_called_once_with("echo hi")
        process.stdin.close.assert_called_once_with()

    def test_copy_to_system_clipboard_returns_false_when_command_missing(self) -> None:
        with mock.patch.object(_clipboard, "clipboard_command", return_value=None):
            copied = _clipboard.copy_to_system_clipboard("echo hi")

        self.assertFalse(copied)

    def test_clipboard_command_prefers_wl_copy_on_linux(self) -> None:
        with (
            mock.patch("aicage.runtime.menu.textual._clipboard.platform.system", return_value="Linux"),
            mock.patch("aicage.runtime.menu.textual._clipboard.shutil.which") as which_mock,
        ):
            which_mock.side_effect = lambda name: "/usr/bin/wl-copy" if name == "wl-copy" else None

            command = _clipboard.clipboard_command()

        self.assertEqual(["wl-copy"], command)
