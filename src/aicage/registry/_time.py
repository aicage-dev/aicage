from datetime import UTC, datetime


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
