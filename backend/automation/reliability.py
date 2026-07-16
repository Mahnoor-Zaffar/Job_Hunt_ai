"""Reliability enhancements for the automation platform.

Provides cleanup guarantees, timeout defaults, memory leak prevention,
and browser lifecycle management to ensure the automation platform
can run for extended periods without resource exhaustion.
"""

import asyncio
import gc
import logging
import signal
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from typing import Any

logger = logging.getLogger("job_hunting.automation.reliability")

DEFAULT_TIMEOUTS = {
    "navigation": 30,
    "selector_wait": 15,
    "click": 10,
    "fill": 10,
    "upload": 20,
    "submit": 15,
    "screenshot": 10,
}


class AutomationTimeout:
    def __init__(self, config: dict[str, int] | None = None) -> None:
        self._config = config or DEFAULT_TIMEOUTS

    def get(self, key: str, default: int = 10) -> int:
        return self._config.get(key, default)

    def override(self, key: str, value: int) -> None:
        self._config[key] = value


@asynccontextmanager
async def browser_session(browser: Any) -> AsyncGenerator[Any]:
    context = None
    try:
        context = await browser.new_context()
        yield context
    finally:
        if context:
            try:
                await browser.release_context(context)
            except Exception as exc:
                logger.warning("Failed to release context: %s", exc)
        gc.collect()


@asynccontextmanager
async def page_session(browser: Any, context: Any) -> AsyncGenerator[Any]:
    page = None
    try:
        page = await browser.new_page(context)
        yield page
    finally:
        if page:
            try:
                await browser.release_page(page)
            except Exception as exc:
                logger.warning("Failed to release page: %s", exc)


def register_shutdown_handler(browser: Any) -> None:
    async def _cleanup() -> None:
        logger.info("Shutdown signal received — cleaning up browser")
        await browser.close()

    def _handler(signum: int, frame: Any) -> None:
        task = asyncio.create_task(_cleanup())  # noqa: F841

    for sig in (signal.SIGTERM, signal.SIGINT):
        with suppress(Exception):
            signal.signal(sig, _handler)


def get_memory_stats() -> dict[str, int]:
    import sys

    return {
        "object_count": len(gc.get_objects()),
        "garbage_count": len(gc.garbage),
        "refcount_total": sys.gettotalrefcount() if hasattr(sys, "gettotalrefcount") else 0,
    }


async def force_garbage_collection() -> None:
    gc.collect()
    await asyncio.sleep(0.1)
    gc.collect()
