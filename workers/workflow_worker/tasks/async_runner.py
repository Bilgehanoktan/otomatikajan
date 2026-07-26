from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from collections.abc import Coroutine
from typing import Any


logger = logging.getLogger(__name__)


async def _run_with_cleanup(coro: Coroutine[Any, Any, Any]) -> Any:
    try:
        return await coro
    finally:
        try:
            from libs.db.session import close_db

            await close_db()
        except Exception as exc:
            logger.warning("Worker async resource cleanup failed: %s", exc)


def _run_in_new_loop(coro: Coroutine[Any, Any, Any]) -> Any:
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_run_with_cleanup(coro))
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        loop.close()
        asyncio.set_event_loop(None)


def run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    """Run one Celery coroutine and close loop-bound resources before exit."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(_run_in_new_loop, coro).result()

    return _run_in_new_loop(coro)
