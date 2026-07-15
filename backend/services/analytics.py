"""Analytics service providing aggregated metrics for dashboards.

Gathers statistics from multiple repositories and returns
pre-computed summaries suitable for API responses.
"""

import logging
from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select

from backend.models.application import Application
from backend.models.job import Job
from backend.repositories.application import ApplicationRepository
from backend.repositories.infrastructure import ScrapeLogRepository
from backend.repositories.job import JobRepository
from backend.services.base import BaseService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("job_hunting.services.analytics")


class AnalyticsService(BaseService):
    """Computes dashboard-level analytics across the domain."""

    def __init__(
        self,
        job_repo: JobRepository,
        app_repo: ApplicationRepository,
        log_repo: ScrapeLogRepository,
    ) -> None:
        super().__init__()
        self._jobs = job_repo
        self._apps = app_repo
        self._logs = log_repo

    async def get_dashboard_stats(self) -> dict[str, Any]:
        active = await self._jobs.count_active()

        return {
            "total_jobs": active,
            "active_jobs": active,
        }

    async def get_jobs_by_source(self) -> list[dict[str, Any]]:
        session: AsyncSession = self._jobs.session
        query = (
            select(Job.source, func.count())
            .where(Job.status == "active")
            .group_by(Job.source)
            .order_by(func.count().desc())
        )
        result = await session.execute(query)
        return [{"source": str(row[0]), "count": row[1]} for row in result if row[0] is not None]

    async def get_applications_by_status(self) -> list[dict[str, Any]]:
        session: AsyncSession = self._apps.session
        query = (
            select(Application.status, func.count())
            .group_by(Application.status)
            .order_by(func.count().desc())
        )
        result = await session.execute(query)
        return [{"status": str(row[0]), "count": row[1]} for row in result if row[0] is not None]

    async def get_scrape_health(self, limit: int = 10) -> list[dict[str, Any]]:
        logs = await self._logs.get_recent(limit=limit)
        return [
            {
                "source": log.source,
                "status": log.status,
                "jobs_discovered": log.jobs_discovered,
                "jobs_new": log.jobs_new,
                "duration_seconds": log.duration_seconds,
                "started_at": log.started_at.isoformat() if log.started_at else None,
                "error": log.error_message,
            }
            for log in logs
        ]

    async def get_full_dashboard(self) -> dict[str, Any]:
        return {
            "stats": await self.get_dashboard_stats(),
            "jobs_by_source": await self.get_jobs_by_source(),
            "applications_by_status": await self.get_applications_by_status(),
            "recent_scrapes": await self.get_scrape_health(limit=5),
        }
