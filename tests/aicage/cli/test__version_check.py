import io
import json
from unittest import TestCase, mock

from aicage.cli import _version_check as version_check


class _ContextBytesIO(io.BytesIO):
    def __enter__(self) -> "_ContextBytesIO":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


class VersionCheckTests(TestCase):
    def test_check_for_update_rejects_non_http_scheme(self) -> None:
        with mock.patch.object(version_check, "_PYPI_URL", "file:///tmp/example.json"):
            self.assertIsNone(version_check._check_for_update("1.0.0"))

    def test_check_for_update_handles_url_error(self) -> None:
        with mock.patch(
            "aicage.cli._version_check.urllib.request.urlopen",
            side_effect=version_check.urllib.error.URLError("boom"),
        ):
            self.assertIsNone(version_check._check_for_update("1.0.0"))

    def test_check_for_update_handles_bad_json(self) -> None:
        response = _ContextBytesIO(b"not-json")
        with mock.patch(
            "aicage.cli._version_check.urllib.request.urlopen", return_value=response
        ):
            self.assertIsNone(version_check._check_for_update("1.0.0"))

    def test_check_for_update_handles_missing_version(self) -> None:
        payload = json.dumps({"info": {"version": ""}}).encode("utf-8")
        response = _ContextBytesIO(payload)
        with mock.patch(
            "aicage.cli._version_check.urllib.request.urlopen", return_value=response
        ):
            self.assertIsNone(version_check._check_for_update("1.0.0"))

    def test_check_for_update_returns_newer_version(self) -> None:
        payload = json.dumps({"info": {"version": "1.2.0"}}).encode("utf-8")
        response = _ContextBytesIO(payload)
        with mock.patch(
            "aicage.cli._version_check.urllib.request.urlopen", return_value=response
        ):
            self.assertEqual("1.2.0", version_check._check_for_update("1.1.9"))

    def test_is_newer_compares_with_padding(self) -> None:
        self.assertTrue(version_check._is_newer("1.2", "1.1.9"))
        self.assertFalse(version_check._is_newer("1.0", "1.0.0"))

    def test_parse_version_accepts_suffixes(self) -> None:
        self.assertEqual((1, 2, 3), version_check._parse_version("1.2.3-rc1"))
        self.assertIsNone(version_check._parse_version("v1.2.3"))

    def test_run_upgrade_handles_missing_command(self) -> None:
        with (
            mock.patch(
                "aicage.cli._version_check.subprocess.run",
                side_effect=FileNotFoundError("missing"),
            ),
            mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            upgraded = version_check._run_upgrade()

        self.assertFalse(upgraded)
        self.assertIn("Unable to run 'pipx upgrade aicage'", stdout.getvalue())

    def test_run_upgrade_handles_failure(self) -> None:
        result = mock.Mock(returncode=1, stderr="boom")
        with (
            mock.patch("aicage.cli._version_check.subprocess.run", return_value=result),
            mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            upgraded = version_check._run_upgrade()

        self.assertFalse(upgraded)
        self.assertIn(
            "Upgrade failed. Please run 'pipx upgrade aicage' manually.",
            stdout.getvalue(),
        )

    def test_maybe_prompt_update_skips_unknown_version(self) -> None:
        with (
            mock.patch("aicage.cli._version_check._check_for_update") as check_mock,
            mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            updated = version_check.maybe_prompt_update(version_check._UNKNOWN_VERSION)

        self.assertFalse(updated)
        check_mock.assert_not_called()
        self.assertEqual("", stdout.getvalue())

    def test_maybe_prompt_update_no_update(self) -> None:
        with (
            mock.patch(
                "aicage.cli._version_check._check_for_update", return_value=None
            ),
            mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            updated = version_check.maybe_prompt_update("0.1.0")

        self.assertFalse(updated)
        self.assertEqual("", stdout.getvalue())

    def test_maybe_prompt_update_non_tty(self) -> None:
        with (
            mock.patch(
                "aicage.cli._version_check._check_for_update", return_value="1.2.3"
            ),
            mock.patch(
                "aicage.cli._version_check.prompt_update_aicage", return_value=False
            ),
            mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            updated = version_check.maybe_prompt_update("1.0.0")

        self.assertFalse(updated)
        output = stdout.getvalue()
        self.assertIn("Update with: pipx upgrade aicage", output)

    @staticmethod
    def test_maybe_prompt_update_yes_runs_upgrade() -> None:
        with (
            mock.patch(
                "aicage.cli._version_check._check_for_update", return_value="1.2.3"
            ),
            mock.patch(
                "aicage.cli._version_check.prompt_update_aicage", return_value=True
            ),
            mock.patch(
                "aicage.cli._version_check._run_upgrade", return_value=True
            ) as upgrade_mock,
        ):
            updated = version_check.maybe_prompt_update("1.0.0")

        assert updated
        upgrade_mock.assert_called_once()
