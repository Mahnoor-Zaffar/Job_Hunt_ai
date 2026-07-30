from __future__ import annotations

import logging
import uuid

from backend.repositories.application import ApplicationRepository
from backend.services.apply_review import ApplyReviewService

logger = logging.getLogger("job_hunting.apply_scheduler")

APPLIED_STATES = {"submitted", "under_review", "interview", "offer", "rejected", "withdrawn"}


class ApplyScheduler:

    def __init__(self, db) -> None:
        self._db = db
        self._app_repo = ApplicationRepository(db)

    async def run(self, user_id: uuid.UUID, target_count: int = 5) -> dict:
        from sqlalchemy import select
        from backend.models.job import Job

        result = await self._db.execute(
            select(Job)
            .where(Job.status == "active", Job.is_remote, Job.apply_url.isnot(None))
            .order_by(Job.posted_at.desc().nulls_last())
            .limit(200)
        )
        remote_jobs = list(result.scalars().all())

        existing_apps = await self._app_repo.get_by_user(user_id, skip=0, limit=500)
        applied_job_ids = {str(a.job_id) for a in existing_apps if a.status in APPLIED_STATES}

        candidates = [j for j in remote_jobs if str(j.id) not in applied_job_ids]
        candidates.sort(
            key=lambda j: j.posted_at or j.created_at,
            reverse=True,
        )

        review_svc = ApplyReviewService(self._db)
        prepared = 0
        skipped = 0

        for job in candidates[: target_count * 2]:
            if prepared >= target_count:
                break
            if not job.apply_url:
                skipped += 1
                continue
            try:
                await review_svc.prepare_application(user_id, job.id)
                prepared += 1
            except Exception:
                logger.exception("Failed to prepare application for job %s", job.id)
                skipped += 1

        logger.info("Scheduler prepared %d applications (skipped %d)", prepared, skipped)
        return {
            "prepared": prepared,
            "skipped": skipped,
            "target": target_count,
        }
