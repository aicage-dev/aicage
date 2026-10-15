"""Run the WSL Docker CLI from a Windows process.

Used only by the Windows integration workflow. Docker bind-mount source paths
need translating from Windows paths to their WSL-mounted equivalents.
"""

import os
import re
import subprocess
import sys


def convert_windows_path(path: str) -> str:
    """Translate an absolute Windows path to its standard WSL mount path."""
    match = re.match(r"^([A-Za-z]):[\\/](.*)$", path)
    if not match:
        return path
    tail = match.group(2).replace("\\", "/")
    return f"/mnt/{match.group(1).lower()}/{tail}"


def convert_mount_value(value: str) -> str:
    """Translate a bind-mount source in Docker's --mount syntax."""
    return re.sub(
        r"(^|,)src=([A-Za-z]:[\\/][^,]*)",
        lambda match: f"{match.group(1)}src={convert_windows_path(match.group(2))}",
        value,
    )


def convert_volume_value(value: str) -> str:
    """Translate a bind-mount source in Docker's --volume syntax."""
    match = re.match(r"^([A-Za-z]:[\\/][^:]*)(:.*)$", value)
    if not match:
        return value
    return f"{convert_windows_path(match.group(1))}{match.group(2)}"


def translate_args(args: list[str]) -> list[str]:
    """Translate Windows host paths in Docker CLI arguments for WSL."""
    translated: list[str] = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg in {"--mount", "--volume", "-v", "--file"}:
            if index + 1 >= len(args):
                raise ValueError(f"Missing value for Docker argument {arg}.")
            value = args[index + 1]
            translated.append(arg)
            if arg == "--mount":
                translated.append(convert_mount_value(value))
            elif arg in {"--volume", "-v"}:
                translated.append(convert_volume_value(value))
            else:
                translated.append(convert_windows_path(value))
            index += 2
            continue
        if arg.startswith("--mount="):
            translated.append(f"--mount={convert_mount_value(arg[8:])}")
        else:
            translated.append(convert_windows_path(arg))
        index += 1
    return translated


def main(args: list[str]) -> int:
    """Invoke Docker in the configured WSL distribution."""
    distribution = os.environ["AICAGE_WSL_DISTRIBUTION"]
    result = subprocess.run(  # nosec B603 -- command and arguments are fixed by the CI workflow.
        [
            "wsl.exe",
            "-d",
            distribution,
            "-u",
            "root",
            "--",
            "env",
            "-u",
            "DOCKER_HOST",
            "docker",
            *translate_args(args),
        ],
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
