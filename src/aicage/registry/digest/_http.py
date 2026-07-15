import urllib.error
import urllib.request
from collections.abc import Mapping

from aicage._logging import get_logger
from aicage._network import (
    classify_network_failure,
    host_from_url,
    require_http_url,
)
from aicage.constants import REGISTRY_DIGEST_REQUEST_TIMEOUT_SECONDS


def head_request(
    url: str, headers: Mapping[str, str]
) -> tuple[int | None, dict[str, str]]:
    logger = get_logger()
    try:
        request = urllib.request.Request(
            require_http_url(url), headers=dict(headers), method="HEAD"
        )
        with urllib.request.urlopen(  # nosec B310 -- request URL is restricted to HTTP(S) by require_http_url().
            request, timeout=REGISTRY_DIGEST_REQUEST_TIMEOUT_SECONDS
        ) as response:
            return response.status, dict(response.headers)
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers)
    except urllib.error.URLError as exc:
        logger.warning(
            "Network request failed (operation=registry_digest_head, host=%s, category=%s).",
            host_from_url(url),
            classify_network_failure(exc),
        )
        return None, {}
    except TimeoutError:
        logger.warning(
            "Network request failed (operation=registry_digest_head, host=%s, category=timeout).",
            host_from_url(url),
        )
        return None, {}


def get_header(headers: Mapping[str, str], key: str) -> str | None:
    for header, value in headers.items():
        if header.lower() == key:
            return value
    return None
