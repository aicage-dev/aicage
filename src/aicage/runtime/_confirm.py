import sys

from aicage.runtime._errors import RuntimeExecutionError


def prompt_update_aicage(installed_version: str, latest_version: str) -> bool:
    question = (
        "A newer version of aicage is available "
        f"(installed: {installed_version}, latest: {latest_version}). "
        "Update now?"
    )
    return _prompt_yes_no(question, default=True)


def _prompt_yes_no(question: str, default: bool = False) -> bool:
    _ensure_tty()
    suffix = "[Y/n]" if default else "[y/N]"
    response = input(f"{question} {suffix} ").strip().lower()
    if not response:
        return default
    return response in {"y", "yes"}


def _ensure_tty() -> None:
    if sys.stdin.isatty():
        return
    raise RuntimeExecutionError("Interactive confirmation requires a terminal.")
