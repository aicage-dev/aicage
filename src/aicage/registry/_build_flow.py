from collections.abc import Callable
from typing import TypeVar

_T = TypeVar("_T")


def maybe_build(
    load_record: Callable[[], _T | None],
    should_rebuild: Callable[[_T | None], bool],
    run_build: Callable[[], None],
    save_record: Callable[[], object],
) -> bool:
    record = load_record()
    if not should_rebuild(record):
        return False
    run_build()
    save_record()
    return True
