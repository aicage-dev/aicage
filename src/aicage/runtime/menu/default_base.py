import sys
from pathlib import Path

from aicage.constants import DEFAULT_IMAGE_BASE

_OS_RELEASE_PATH: Path = Path("/etc/os-release")


def resolve_default_base(available_bases: list[str]) -> str:
    if not available_bases:
        return DEFAULT_IMAGE_BASE
    for candidate in _preferred_bases_for_host():
        matched = _find_matching_base(candidate, available_bases)
        if matched is not None:
            return matched
    if DEFAULT_IMAGE_BASE in available_bases:
        return DEFAULT_IMAGE_BASE
    return available_bases[0]


def _preferred_bases_for_host() -> list[str]:
    if not sys.platform.startswith("linux"):
        return [DEFAULT_IMAGE_BASE]
    return _host_distro_tokens()


def _host_distro_tokens() -> list[str]:
    data = _read_os_release()
    tokens: list[str] = []
    distro_id = data.get("id")
    id_like = data.get("id_like")
    if distro_id:
        token = distro_id.strip().lower()
        if token:
            tokens.append(token)
    if id_like:
        for raw_token in id_like.split():
            token = raw_token.strip().lower()
            if token:
                tokens.append(token)
    return tokens


def _read_os_release() -> dict[str, str]:
    try:
        content = _OS_RELEASE_PATH.read_text(encoding="utf-8")
    except OSError:
        return {}
    values: dict[str, str] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip().lower()
        value = value.strip().strip("\"'")
        if key:
            values[key] = value.lower()
    return values


def _find_matching_base(candidate: str, available_bases: list[str]) -> str | None:
    candidate_lower = candidate.lower()
    for base in available_bases:
        if base.lower() == candidate_lower:
            return base
    return None
