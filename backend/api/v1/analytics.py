"""Analytics and dashboard statistics endpoints."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db
from backend.models.application import Application
from backend.models.job import Job
from backend.models.scrape_log import ScrapeLog
from backend.schemas.base import BaseSchema

router = APIRouter(prefix="/analytics", tags=["analytics"])


class DashboardStats(BaseSchema):
    total_jobs: int
    active_jobs: int
    applications_submitted: int
    interviews_scheduled: int
    offers_received: int
    companies_tracked: int
    last_scrape: datetime | None = None
    jobs_today: int = 0
    new_this_week: int = 0


class SourceBreakdown(BaseSchema):
    source: str
    count: int


class AnalyticsResponse(BaseSchema):
    stats: DashboardStats
    jobs_by_source: list[SourceBreakdown] = Field(default_factory=list)
    applications_by_status: list[SourceBreakdown] = Field(default_factory=list)
    jobs_by_location: list[SourceBreakdown] = Field(default_factory=list)


@router.get("/dashboard", response_model=AnalyticsResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> AnalyticsResponse:
    stats = DashboardStats(
        total_jobs=await _count(db, Job),
        active_jobs=await _count(db, Job, where=Job.status == "active"),
        applications_submitted=await _count(
            db, Application, where=Application.status == "submitted"
        ),
        interviews_scheduled=await _count(db, Application, where=Application.status == "interview"),
        offers_received=await _count(db, Application, where=Application.status == "offer"),
        companies_tracked=0,
    )

    last_log = await db.execute(
        select(ScrapeLog.finished_at).order_by(ScrapeLog.finished_at.desc().nullslast()).limit(1)
    )
    stats.last_scrape = last_log.scalar_one_or_none()

    jobs_by_source = await _group_by(db, Job, Job.source)
    apps_by_status = await _group_by(db, Application, Application.status)

    return AnalyticsResponse(
        stats=stats,
        jobs_by_source=[SourceBreakdown(source=s, count=c) for s, c in jobs_by_source],
        applications_by_status=[SourceBreakdown(source=s, count=c) for s, c in apps_by_status],
    )


async def _count(db: AsyncSession, model: type[Any], where: Any = None) -> int:
    query = select(func.count()).select_from(model)
    if where is not None:
        query = query.where(where)
    result = await db.execute(query)
    return result.scalar_one() or 0


async def _group_by(db: AsyncSession, model: type[Any], column: Any) -> list[tuple[str, int]]:
    query = select(column, func.count()).group_by(column).order_by(func.count().desc())
    result = await db.execute(query)
    return [(str(row[0]), row[1]) for row in result if row[0] is not None]
