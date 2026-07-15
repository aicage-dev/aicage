import urllib.error
from unittest import TestCase, mock

from aicage.registry.digest import _http


class DigestHttpTests(TestCase):
    def test_get_header_returns_match(self) -> None:
        value = _http.get_header({"Content-Type": "text/plain"}, "content-type")

        self.assertEqual("text/plain", value)

    def test_head_request_returns_none_on_url_error(self) -> None:
        with mock.patch(
            "aicage.registry.digest._http.urllib.request.urlopen",
            side_effect=urllib.error.URLError("boom"),
        ):
            status, headers = _http.head_request(
                "https://example.test", {"Accept": "x"}
            )
        self.assertIsNone(status)
        self.assertEqual({}, headers)

    def test_head_request_returns_none_on_timeout_error(self) -> None:
        with mock.patch(
            "aicage.registry.digest._http.urllib.request.urlopen",
            side_effect=TimeoutError("timed out"),
        ):
            status, headers = _http.head_request(
                "https://example.test", {"Accept": "x"}
            )
        self.assertIsNone(status)
        self.assertEqual({}, headers)

    def test_head_request_rejects_non_http_scheme(self) -> None:
        status, headers = _http.head_request("file:///tmp/example.json", {"Accept": "x"})

        self.assertIsNone(status)
        self.assertEqual({}, headers)
