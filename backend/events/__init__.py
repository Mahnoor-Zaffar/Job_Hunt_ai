"""Lightweight event bus for decoupled publish/subscribe messaging.

Domain services emit events and notification handlers subscribe
to them.  This keeps the notification system fully decoupled from
business logic — services never call notifiers directly.
"""

import asyncio
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("job_hunting.events")


@dataclass
class DomainEvent:
    """Immutable event payload."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


Handler = Callable[[DomainEvent], Awaitable[None]]

_subscribers: dict[str, list[Handler]] = defaultdict(list)


def subscribe(event_name: str, handler: Handler) -> None:
    _subscribers[event_name].append(handler)
    logger.debug("Subscribed handler to event '%s'", event_name)


def unsubscribe(event_name: str, handler: Handler) -> None:
    handlers = _subscribers.get(event_name, [])
    if handler in handlers:
        handlers.remove(handler)


async def publish(event: DomainEvent) -> None:
    handlers = _subscribers.get(event.name, [])
    if not handlers:
        return
    logger.debug("Publishing event '%s' to %d handler(s)", event.name, len(handlers))
    tasks = [h(event) for h in handlers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, Exception):
            logger.error("Event handler failed: %s", r)


# -- Pre-defined event names -----------------------------------------------
NEW_JOB_DISCOVERED = "job.new"
JOB_MATCHED = "job.matched"
WATCHLIST_COMPANY_OPENING = "watchlist.new_opening"
SCRAPER_FAILED = "scraper.failed"
APPLICATION_SUBMITTED = "application.submitted"
APPLICATION_STATUS_CHANGED = "application.status_changed"
RESUME_UPDATED = "resume.updated"
FOLLOW_UP_REMINDER = "application.reminder"

__all__ = [
    "APPLICATION_STATUS_CHANGED",
    "APPLICATION_SUBMITTED",
    "FOLLOW_UP_REMINDER",
    "JOB_MATCHED",
    "NEW_JOB_DISCOVERED",
    "RESUME_UPDATED",
    "SCRAPER_FAILED",
    "WATCHLIST_COMPANY_OPENING",
    "DomainEvent",
    "publish",
    "subscribe",
    "unsubscribe",
]
