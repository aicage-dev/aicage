import os
import subprocess
from pathlib import Path


def resolve_host_timezone() -> str | None:
    env_timezone = os.environ.get("TZ")
    if env_timezone:
        return env_timezone

    if os.name == "nt":
        return _resolve_windows_timezone()

    return _resolve_posix_timezone()


def _resolve_posix_timezone() -> str | None:
    timezone_file = Path("/etc/timezone")
    if timezone_file.is_file():
        timezone = timezone_file.read_text(encoding="utf-8").strip()
        if timezone:
            return timezone

    localtime_path = Path("/etc/localtime")
    if not localtime_path.exists():
        return None

    resolved = localtime_path.resolve()
    parts = resolved.parts
    if "zoneinfo" not in parts:
        return None

    zoneinfo_index = parts.index("zoneinfo")
    timezone_parts = parts[zoneinfo_index + 1 :]
    if not timezone_parts:
        return None

    return "/".join(timezone_parts)


def _resolve_windows_timezone() -> str | None:
    command = (
        "[System.TimeZoneInfo]::TryConvertWindowsIdToIanaId("
        "[System.TimeZoneInfo]::Local.Id, [ref]$iana) | Out-Null; "
        "$iana"
    )
    for shell in ("powershell", "pwsh"):
        try:
            result = subprocess.run(
                [shell, "-NoProfile", "-Command", command],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError:
            continue
        timezone = result.stdout.strip()
        if result.returncode == 0 and timezone:
            return timezone
    return None
