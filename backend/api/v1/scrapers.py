from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import Field

from backend.schemas.base import BaseSchema
from backend.scrapers.orchestrator.orchestrator import ScraperOrchestrator
from backend.scrapers.registry.registry import ScraperRegistry

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


@router.get("", response_model=ScrapersListResponse)
async def list_scrapers() -> ScrapersListResponse:
    """Return all registered scrapers with metadata."""
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
    """Trigger a scraping run (all scrapers or a specific source)."""
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
