"""Real-time scraper status API — polling endpoint for dashboard."""

from typing import Any

from fastapi import APIRouter
from pydantic import Field

from backend.schemas.base import BaseSchema

router = APIRouter(prefix="/scrapers", tags=["scrapers"])


class ScraperStatusItem(BaseSchema):
    source: str
    display_name: str
    last_run: str | None = None
    last_status: str = "unknown"
    last_jobs: int = 0
    last_duration: float = 0.0
    last_error: str | None = None


class ScraperStatusResponse(BaseSchema):
    scrapers: list[ScraperStatusItem] = Field(default_factory=list)
    total_jobs: int = 0
    running: bool = False


@router.get("/status", response_model=ScraperStatusResponse)
async def scraper_status() -> ScraperStatusResponse:
    from backend.database.session import get_session_factory
    from backend.repositories.infrastructure import ScrapeLogRepository
    from backend.repositories.job import JobRepository

    factory = get_session_factory()
    scrapers: list[ScraperStatusItem] = []

    async with factory() as session:
        log_repo = ScrapeLogRepository(session)
        job_repo = JobRepository(session)

        recent_logs = await log_repo.get_recent(limit=20)
        source_map: dict[str, dict[str, Any]] = {}
        for log in recent_logs:
            if log.source not in source_map:
                source_map[log.source] = {
                    "status": log.status,
                    "jobs": log.jobs_new,
                    "duration": log.duration_seconds,
                    "error": log.error_message,
                    "finished_at": log.finished_at.isoformat() if log.finished_at else None,
                }

        from backend.scrapers.registry.registry import ScraperRegistry

        registry = ScraperRegistry()
        sources = registry.list_sources()

        for s in sources:
            src = str(s.get("source", ""))
            info = source_map.get(src, {})
            scrapers.append(
                ScraperStatusItem(
                    source=src,
                    display_name=str(s.get("display_name", src)),
                    last_run=info.get("finished_at"),
                    last_status=info.get("status", "unknown"),
                    last_jobs=info.get("jobs", 0),
                    last_duration=info.get("duration", 0.0),
                    last_error=info.get("error"),
                )
            )

        total = await job_repo.count_active()

    return ScraperStatusResponse(scrapers=scrapers, total_jobs=total)
