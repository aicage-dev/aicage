import socket
import ssl
import urllib.error
from urllib.parse import urlparse

_HTTP_PROXY_AUTH_REQUIRED: int = 407
_HTTP_AUTH_STATUS_CODES: set[int] = {401, 403}
_SUPPORTED_URL_SCHEMES: set[str] = {"http", "https"}


def classify_network_failure(exc: BaseException) -> str:
    category = "unknown"
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code == _HTTP_PROXY_AUTH_REQUIRED:
            category = "proxy_auth_407"
        elif exc.code in _HTTP_AUTH_STATUS_CODES:
            category = "auth_401_403"
        else:
            category = "http_error"
    elif isinstance(exc, urllib.error.URLError):
        category = _classify_url_error_reason(exc.reason)
    elif isinstance(exc, socket.gaierror):
        category = "dns"
    elif isinstance(exc, (socket.timeout, TimeoutError)):
        category = "connect_or_timeout"
    elif isinstance(exc, ssl.SSLCertVerificationError):
        category = "tls"
    elif isinstance(exc, ssl.SSLError):
        category = "tls"
    elif isinstance(exc, OSError):
        category = "connect_or_timeout"
    return category


def host_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.hostname:
        return parsed.hostname
    return url


def require_http_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in _SUPPORTED_URL_SCHEMES:
        raise urllib.error.URLError(
            f"Unsupported URL scheme for network request: {parsed.scheme or '<missing>'}"
        )
    return url


def _classify_url_error_reason(reason: object) -> str:
    if isinstance(reason, socket.gaierror):
        return "dns"
    if isinstance(reason, ssl.SSLCertVerificationError):
        return "tls"
    if isinstance(reason, ssl.SSLError):
        return "tls"
    if isinstance(reason, (socket.timeout, TimeoutError)):
        return "connect_or_timeout"
    if isinstance(reason, OSError):
        return "connect_or_timeout"
    return "unknown"
