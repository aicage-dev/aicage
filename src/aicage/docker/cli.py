import subprocess  # nosec B404 -- subprocess is the intended wrapper for Docker CLI execution.
from typing import Literal, TextIO, overload

from aicage.docker.errors import DockerError


def run_docker_command(
    command: list[str],
    *,
    check: bool,
    stdout: TextIO | int | None = None,
    stderr: TextIO | int | None = None,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(  # nosec B603 -- command is a caller-built Docker CLI argv list without shell usage.
            command,
            check=check,
            stdout=stdout,
            stderr=stderr,
        )
    except FileNotFoundError as exc:
        raise DockerError(
            "Docker CLI not found. Install Docker and ensure it is on PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise DockerError(
            f"Docker command failed with exit code {exc.returncode}."
        ) from exc


@overload
def run_docker_command_capture(
    command: list[str],
    *,
    check: bool,
    text: Literal[True],
) -> subprocess.CompletedProcess[str]: ...


@overload
def run_docker_command_capture(
    command: list[str],
    *,
    check: bool,
    text: Literal[False],
) -> subprocess.CompletedProcess[bytes]: ...


def run_docker_command_capture(
    command: list[str],
    *,
    check: bool,
    text: bool,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(  # nosec B603 -- command is a caller-built Docker CLI argv list without shell usage.
            command,
            check=check,
            capture_output=True,
            text=text,
        )
    except FileNotFoundError as exc:
        raise DockerError(
            "Docker CLI not found. Install Docker and ensure it is on PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise DockerError(
            f"Docker command failed with exit code {exc.returncode}."
        ) from exc
