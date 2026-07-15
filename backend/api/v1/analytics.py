"""Analytics API — dashboard metrics and reports."""

from datetime import datetime, timedelta
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
    companies_tracked: int = 0
    last_scrape: datetime | None = None
    jobs_today: int = 0
    new_this_week: int = 0


class SourceBreakdown(BaseSchema):
    source: str
    count: int


class HiringTrend(BaseSchema):
    month: str
    count: int


class ReportResponse(BaseSchema):
    stats: DashboardStats
    jobs_by_source: list[SourceBreakdown] = Field(default_factory=list)
    applications_by_status: list[SourceBreakdown] = Field(default_factory=list)
    jobs_by_location: list[SourceBreakdown] = Field(default_factory=list)
    hiring_trends: list[HiringTrend] = Field(default_factory=list)
    top_technologies: list[SourceBreakdown] = Field(default_factory=list)
    recent_scrapes: list[dict[str, Any]] = Field(default_factory=list)


@router.get("/dashboard", response_model=ReportResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """Full analytics dashboard with all statistics."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    stats = DashboardStats(
        total_jobs=await _count(db, Job),
        active_jobs=await _count(db, Job, where=Job.status == "active"),
        applications_submitted=await _count(
            db, Application, where=Application.status == "submitted"
        ),
        interviews_scheduled=await _count(db, Application, where=Application.status == "interview"),
        offers_received=await _count(db, Application, where=Application.status == "offer"),
        jobs_today=await _count(db, Job, where=Job.created_at >= today_start),
        new_this_week=await _count(db, Job, where=Job.created_at >= week_start),
    )

    last_log = await db.execute(
        select(ScrapeLog.finished_at)
        .where(ScrapeLog.finished_at.isnot(None))
        .order_by(ScrapeLog.finished_at.desc())
        .limit(1)
    )
    stats.last_scrape = last_log.scalar_one_or_none()

    jobs_by_source = await _group_by(db, Job, Job.source)
    apps_by_status = await _group_by(db, Application, Application.status)
    jobs_by_location = await _group_by(db, Job, Job.city)

    hiring_trends = await _hiring_trends(db)

    tech_query = select(Job.skills).where(Job.skills.isnot(None))
    tech_result = await db.execute(tech_query)
    tech_counter: dict[str, int] = {}
    for (skills,) in tech_result:
        if isinstance(skills, list):
            for skill in skills:
                tech_counter[skill] = tech_counter.get(skill, 0) + 1
    top_tech = sorted(tech_counter.items(), key=lambda x: x[1], reverse=True)[:15]

    recent_logs_result = await db.execute(
        select(ScrapeLog).order_by(ScrapeLog.started_at.desc()).limit(10)
    )
    recent_logs = recent_logs_result.scalars().all()
    recent_scrapes = [
        {
            "source": log.source,
            "status": log.status,
            "jobs_found": log.jobs_new,
            "duration_seconds": round(log.duration_seconds, 2),
            "finished_at": log.finished_at.isoformat() if log.finished_at else None,
        }
        for log in recent_logs
    ]

    return ReportResponse(
        stats=stats,
        jobs_by_source=[SourceBreakdown(source=str(s), count=c) for s, c in jobs_by_source],
        applications_by_status=[SourceBreakdown(source=str(s), count=c) for s, c in apps_by_status],
        jobs_by_location=[
            SourceBreakdown(source=str(s) if s else "Unknown", count=c) for s, c in jobs_by_location
        ],
        hiring_trends=[HiringTrend(month=m, count=c) for m, c in hiring_trends],
        top_technologies=[SourceBreakdown(source=s, count=c) for s, c in top_tech],
        recent_scrapes=recent_scrapes,
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


async def _hiring_trends(db: AsyncSession) -> list[tuple[str, int]]:
    from sqlalchemy import extract as sa_extract

    query = (
        select(
            sa_extract("year", Job.created_at).label("year"),
            sa_extract("month", Job.created_at).label("month"),
            func.count(),
        )
        .where(Job.created_at.isnot(None))
        .group_by("year", "month")
        .order_by("year", "month")
        .limit(12)
    )
    result = await db.execute(query)
    return [(f"{int(row[0])}-{int(row[1]):02d}", row[2]) for row in result]
