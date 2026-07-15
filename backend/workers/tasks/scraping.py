from typing import Any

from celery.utils.log import get_task_logger

from backend.scrapers.orchestrator.orchestrator import ScraperOrchestrator
from backend.workers.celery_app import celery_app

logger = get_task_logger(__name__)


@celery_app.task(  # type: ignore[untyped-decorator]
    bind=True,
    name="run_all_scrapers",
    max_retries=2,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    acks_late=True,
)
def run_all_scrapers(self: Any) -> dict[str, Any]:
    logger.info("Running all enabled scrapers (task id=%s)", self.request.id)
    orchestrator = ScraperOrchestrator()

    import asyncio

    summary = asyncio.get_event_loop().run_until_complete(orchestrator.run_all())

    logger.info(
        "Scraping complete: %d succeeded, %d failed, %d jobs",
        summary.succeeded,
        summary.failed,
        summary.total_jobs,
    )
    return {
        "succeeded": summary.succeeded,
        "failed": summary.failed,
        "total_jobs": summary.total_jobs,
        "duration_seconds": summary.duration_seconds,
    }
