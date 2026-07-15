"""Celery tasks for asynchronous notifications.

These tasks are triggered by domain events and run in background
workers.  They never block the API or scraping pipeline.
"""

from typing import Any

from celery.utils.log import get_task_logger

from backend.events import (
    APPLICATION_STATUS_CHANGED,
    APPLICATION_SUBMITTED,
    FOLLOW_UP_REMINDER,
    JOB_MATCHED,
    NEW_JOB_DISCOVERED,
    SCRAPER_FAILED,
    WATCHLIST_COMPANY_OPENING,
    DomainEvent,
    subscribe,
)
from backend.notifications.telegram import TelegramNotifier
from backend.workers.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(  # type: ignore[untyped-decorator]
    name="notify_new_jobs",
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def notify_new_jobs(event_data: dict[str, Any]) -> None:
    """Send notification when new matching jobs are discovered."""
    notifier = TelegramNotifier()
    if not notifier.is_configured:
        return

    import asyncio

    async def _send() -> None:
        alerts: list[dict[str, Any]] = event_data.get("jobs", [])
        sent = await notifier.send_batch(alerts)
        logger.info("Sent %d new-job alerts via Telegram", sent)

    asyncio.get_event_loop().run_until_complete(_send())


@celery_app.task(  # type: ignore[untyped-decorator]
    name="notify_watchlist_opening",
    max_retries=2,
    acks_late=True,
)
def notify_watchlist_opening(event_data: dict[str, Any]) -> None:
    """Send notification when a watchlist company posts a new job."""
    notifier = TelegramNotifier()
    if not notifier.is_configured:
        return

    import asyncio

    async def _send() -> None:
        await notifier.send_job_alert(
            title=str(event_data.get("title", "")),
            company=str(event_data.get("company", "")),
            location=str(event_data.get("location", "")),
            url=str(event_data.get("url", "")),
            salary=event_data.get("salary"),
            skills=event_data.get("skills"),
        )

    asyncio.get_event_loop().run_until_complete(_send())


@celery_app.task(  # type: ignore[untyped-decorator]
    name="notify_scraper_failure",
    max_retries=1,
    acks_late=True,
)
def notify_scraper_failure(event_data: dict[str, Any]) -> None:
    """Alert when a scraper fails."""
    notifier = TelegramNotifier()
    if not notifier.is_configured:
        return

    import asyncio

    async def _send() -> None:
        source = event_data.get("source", "unknown")
        error = event_data.get("error", "unknown error")
        await notifier.send_message(
            f"\N{ROBOT FACE} <b>Scraper Failure</b>\nSource: {source}\nError: {error}"
        )

    asyncio.get_event_loop().run_until_complete(_send())


@celery_app.task(  # type: ignore[untyped-decorator]
    name="notify_application_submitted",
    max_retries=1,
    acks_late=True,
)
def notify_application_submitted(event_data: dict[str, Any]) -> None:
    """Confirm application submission."""
    notifier = TelegramNotifier()
    if not notifier.is_configured:
        return

    import asyncio

    async def _send() -> None:
        await notifier.send_message(
            f"\N{CHECK MARK} <b>Application Submitted</b>\n"
            f"{event_data.get('title', '')} at {event_data.get('company', '')}\n"
            f"Status: {event_data.get('status', 'submitted')}"
        )

    asyncio.get_event_loop().run_until_complete(_send())


@celery_app.task(  # type: ignore[untyped-decorator]
    name="notify_reminder",
    max_retries=1,
    acks_late=True,
)
def notify_reminder(event_data: dict[str, Any]) -> None:
    """Send a follow-up reminder."""
    notifier = TelegramNotifier()
    if not notifier.is_configured:
        return

    import asyncio

    async def _send() -> None:
        await notifier.send_message(
            f"\N{BELL} <b>Reminder</b>\n{event_data.get('message', 'Follow up')}"
        )

    asyncio.get_event_loop().run_until_complete(_send())


# -- Wire event handlers to Celery tasks ----------------------------------


def _dispatch(task: Any) -> Any:
    def _handler(event: DomainEvent) -> None:
        task.delay(event.data)

    return _handler


subscribe(NEW_JOB_DISCOVERED, _dispatch(notify_new_jobs))
subscribe(WATCHLIST_COMPANY_OPENING, _dispatch(notify_watchlist_opening))
subscribe(SCRAPER_FAILED, _dispatch(notify_scraper_failure))
subscribe(APPLICATION_SUBMITTED, _dispatch(notify_application_submitted))
subscribe(APPLICATION_STATUS_CHANGED, _dispatch(notify_application_submitted))
subscribe(JOB_MATCHED, _dispatch(notify_new_jobs))
subscribe(FOLLOW_UP_REMINDER, _dispatch(notify_reminder))
