ROW_BASE = "base"
ROW_EXTENSIONS = "extensions"
ROW_EXTRAS = "extras"
_ROW_SHARES = "shares"

SECTION_IDS: tuple[str, ...] = (ROW_BASE, ROW_EXTENSIONS, _ROW_SHARES, ROW_EXTRAS)


def built_in_selection_key(source: str, key: str) -> str:
    return f"builtin:{source}:{key}"


def built_in_identity(source: str, key: str) -> str:
    return f"{source}:{key}"


def custom_share_selection_key(value: str) -> str:
    return f"custom:{value}"


def docker_selection_key(key: str) -> str:
    return f"docker:{key}"
