import subprocess  # nosec B404 -- subprocess is required to probe helper commands and capture their stdout.
from pathlib import Path


def capture_stdout(command: list[str], cwd: Path | None = None) -> str | None:
    try:
        result = subprocess.run(  # nosec B603 -- command is an explicit argv list without shell usage.
            command,
            check=True,
            capture_output=True,
            text=True,
            cwd=str(cwd) if cwd else None,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout
