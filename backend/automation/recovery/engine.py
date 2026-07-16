"""Recovery engine — retry logic, error handling, graceful degradation.

Handles transient failures (timeouts, network errors, stale elements)
with exponential backoff.  Persistent failures are logged and surfaced
so they can be reviewed by a human.
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("job_hunting.automation.recovery")


class RecoveryConfig:
    def __init__(
        self,
        max_retries: int = 3,
        base_delay_seconds: float = 1.0,
        max_delay_seconds: float = 30.0,
    ) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay_seconds
        self.max_delay = max_delay_seconds


DEFAULT_RECOVERY = RecoveryConfig()


async def with_recovery(
    fn: Callable[..., Any],
    *args: Any,
    recovery: RecoveryConfig | None = None,
    on_retry: Callable[[int, Exception], None] | None = None,
    **kwargs: Any,
) -> Any:
    cfg = recovery or DEFAULT_RECOVERY
    last_error: Exception | None = None

    for attempt in range(cfg.max_retries):
        try:
            return await fn(*args, **kwargs)
        except Exception as exc:
            last_error = exc
            logger.warning("Recovery attempt %d/%d: %s", attempt + 1, cfg.max_retries, exc)
            if on_retry:
                on_retry(attempt + 1, exc)
            if attempt < cfg.max_retries - 1:
                delay = min(cfg.base_delay * (2**attempt), cfg.max_delay)
                await asyncio.sleep(delay)

    raise last_error or RuntimeError("Recovery exhausted")
