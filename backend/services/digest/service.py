import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select

from backend.config.settings import get_settings
from backend.models.job import Job
from backend.notifications.email import EmailNotifier
from backend.repositories.infrastructure import SettingsRepository
from backend.services.digest.config import DigestConfig, get_config
from backend.services.digest.pipeline import run_pipeline, generate_email

logger = logging.getLogger(__name__)

USER_ID = "00000000-0000-0000-0000-000000000001"


class RuleBasedDigestService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        config: DigestConfig | None = None,
    ):
        self._session_factory = session_factory
        self._config = config or get_config()
        self._email_notifier = EmailNotifier()
        self._settings_repo = SettingsRepository()

    def _get_session(self) -> AsyncSession:
        return self._session_factory()

    async def fetch_recent_jobs(self, hours: int = 24) -> list[Job]:
        async with self._get_session() as session:
            since = datetime.now(timezone.utc) - timedelta(hours=hours)
            stmt = (
                select(Job)
                .where(Job.status == "active")
                .where(
                    Job.created_at >= since
                )
                .order_by(Job.created_at.desc())
                .limit(500)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def send_digest(self) -> dict:
        start = time.monotonic()

        async with self._get_session() as session:
            email = await self._settings_repo.get_value(session, USER_ID, "alert.email")
            digest_enabled = await self._settings_repo.get_value(session, USER_ID, "alert.digest_enabled")

        if not self._email_notifier.is_configured():
            logger.warning("Email not configured, skipping digest")
            return {"error": "Email not configured"}

        if not email:
            logger.warning("No email address configured, skipping digest")
            return {"error": "No email address configured"}

        if digest_enabled and digest_enabled.lower() != "true":
            logger.info("Digest disabled by user preference")
            return {"skipped": "Digest disabled"}

        raw_jobs = await self.fetch_recent_jobs(hours=24)
        logger.info("Fetched %d recent jobs", len(raw_jobs))

        if not raw_jobs:
            logger.info("No recent jobs to process")
            return {"skipped": "No recent jobs"}

        result = run_pipeline(raw_jobs, self._config)

        if not result.categories or sum(len(g.jobs) for g in result.categories) == 0:
            logger.info("No matching jobs found for digest")
            return {"skipped": "No matching jobs"}

        html, text = generate_email(result, self._config)

        delivery_start = time.monotonic()
        try:
            success = await asyncio.to_thread(
                self._email_notifier.send,
                to=email,
                subject="Your Daily Job Digest",
                body=html,
                html=True,
            )
            result.email_delivered = success
            if not success:
                result.email_error = "EmailNotifier.send returned False"
                logger.error("Failed to send digest email")
        except Exception as e:
            result.email_delivered = False
            result.email_error = str(e)
            logger.error("Error sending digest email: %s", e)

        total_duration = (time.monotonic() - start) * 1000
        logger.info(
            "Digest complete: %dms total (pipeline: %.1fms, email: %.1fms)",
            total_duration,
            result.processing_duration_ms,
            result.email_generation_ms,
        )

        summary = {
            "total_scraped": result.total_scraped,
            "accepted": result.accepted,
            "rejected": result.rejected,
            "duplicates_removed": result.duplicates_removed,
            "acceptance_rate": result.acceptance_rate,
            "categories": result.per_category_stats,
            "email_delivered": result.email_delivered,
            "duration_ms": total_duration,
        }
        logger.info("Digest summary: %s", summary)
        return summary


async def run_daily_digest(session_factory: async_sessionmaker[AsyncSession]):
    config = get_config()
    service = RuleBasedDigestService(session_factory, config)
    while True:
        try:
            logger.info("Starting daily digest run")
            summary = await service.send_digest()
            logger.info("Daily digest result: %s", summary)
        except Exception as e:
            logger.error("Daily digest failed: %s", e)
        await asyncio.sleep(86400)
