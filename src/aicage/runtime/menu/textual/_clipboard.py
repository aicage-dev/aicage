import platform
import shutil
import subprocess
from collections.abc import Callable

_CLIPBOARD_SETTLE_TIMEOUT_SECONDS = 0.2


def copy_to_clipboard(text: str, fallback: Callable[[str], None]) -> None:
    if copy_to_system_clipboard(text):
        return
    fallback(text)


def copy_to_system_clipboard(text: str) -> bool:
    command = clipboard_command()
    if command is None:
        return False
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        start_new_session=True,
    )
    if process.stdin is None:
        return False
    process.stdin.write(text)
    process.stdin.close()
    try:
        process.wait(timeout=_CLIPBOARD_SETTLE_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return True
    return process.returncode == 0


def clipboard_command() -> list[str] | None:
    system = platform.system()
    if system == "Darwin":
        return ["pbcopy"] if shutil.which("pbcopy") else None
    if system == "Windows":
        return ["clip"] if shutil.which("clip") else None
    for command in (
        ["wl-copy"],
        ["xclip", "-selection", "clipboard"],
        ["xsel", "--clipboard", "--input"],
    ):
        if shutil.which(command[0]):
            return command
    return None
