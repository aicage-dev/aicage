import socket
import ssl
import urllib.error
from email.message import Message
from unittest import TestCase

from aicage._network import classify_network_failure, host_from_url


class NetworkTests(TestCase):
    def test_classify_network_failure_dns(self) -> None:
        error = urllib.error.URLError(socket.gaierror(-2, "Name or service not known"))
        self.assertEqual("dns", classify_network_failure(error))

    def test_classify_network_failure_timeout(self) -> None:
        error = urllib.error.URLError(TimeoutError("timed out"))
        self.assertEqual("connect_or_timeout", classify_network_failure(error))

    def test_classify_network_failure_tls(self) -> None:
        error = urllib.error.URLError(ssl.SSLError("tls failed"))
        self.assertEqual("tls", classify_network_failure(error))

    def test_classify_network_failure_proxy_auth(self) -> None:
        headers = Message()
        error = urllib.error.HTTPError("https://example.test", 407, "Proxy Auth Required", headers, None)
        self.assertEqual("proxy_auth_407", classify_network_failure(error))

    def test_classify_network_failure_auth(self) -> None:
        headers = Message()
        error = urllib.error.HTTPError("https://example.test", 403, "Forbidden", headers, None)
        self.assertEqual("auth_401_403", classify_network_failure(error))

    def test_host_from_url_returns_hostname(self) -> None:
        self.assertEqual("api.github.com", host_from_url("https://api.github.com/repos"))
