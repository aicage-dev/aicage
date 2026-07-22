import asyncio
from typing import Any


def _call_work(app: Any, method_name: str, *args: Any) -> None:
    getattr(app, method_name).__wrapped__(app, *args)


def _call_work_async(app: Any, method_name: str, *args: Any) -> None:
    asyncio.run(getattr(app, method_name).__wrapped__(app, *args))
