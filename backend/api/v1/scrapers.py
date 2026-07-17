"""Scraper API — list, run, status."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import Field

from backend.schemas.base import BaseSchema

router = APIRouter(prefix="/scrapers", tags=["scrapers"])


class ScraperInfo(BaseSchema):
    source: str
    display_name: str
    locations: list[str] = Field(default_factory=list)
    interval_minutes: int = 30
    is_registered: bool = True


class ScrapersListResponse(BaseSchema):
    scrapers: list[ScraperInfo]
    total: int


class RunScrapersRequest(BaseSchema):
    source: str | None = None


class RunScrapersResponse(BaseSchema):
    total_scrapers: int
    succeeded: int
    failed: int
    total_jobs: int
    duration_seconds: float
    results: list[dict[str, Any]] = Field(default_factory=list)


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


@router.get("", response_model=ScrapersListResponse)
async def list_scrapers() -> ScrapersListResponse:
    from backend.scrapers.registry.registry import ScraperRegistry

    registry = ScraperRegistry()
    sources = registry.list_sources()
    items = [
        ScraperInfo(
            source=str(s.get("source", "")),
            display_name=str(s.get("display_name", "")),
            locations=s.get("locations") if isinstance(s.get("locations"), list) else [],
            interval_minutes=int(str(s.get("interval_minutes", 30))),
        )
        for s in sources
    ]
    return ScrapersListResponse(scrapers=items, total=len(items))


@router.post("/run", response_model=RunScrapersResponse)
async def run_scrapers(body: RunScrapersRequest | None = None) -> RunScrapersResponse:
    from backend.scrapers.orchestrator.orchestrator import ScraperOrchestrator

    orchestrator = ScraperOrchestrator()
    source = body.source if body else None

    if source:
        result = await orchestrator.run_single(source)
        if result.error and "Unknown source" in result.error:
            raise HTTPException(status_code=404, detail=result.error)
        return RunScrapersResponse(
            total_scrapers=1,
            succeeded=1 if result.success else 0,
            failed=0 if result.success else 1,
            total_jobs=result.jobs_found,
            duration_seconds=result.duration_seconds,
            results=[result.model_dump()],
        )

    summary = await orchestrator.run_all()
    return RunScrapersResponse(
        total_scrapers=summary.total_scrapers,
        succeeded=summary.succeeded,
        failed=summary.failed,
        total_jobs=summary.total_jobs,
        duration_seconds=summary.duration_seconds,
        results=[r.model_dump() for r in summary.results],
    )


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
