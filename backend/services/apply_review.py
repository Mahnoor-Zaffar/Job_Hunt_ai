from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

from backend.database.session import get_session_factory
from backend.models.application import Application
from backend.models.career_profile import CareerProfile
from backend.models.job import Job
from backend.repositories.application import ApplicationRepository
from backend.repositories.github_repo import GitHubRepoRepository
from backend.services.cover_letter import generate_cover_letter
from backend.services.github_profile import GitHubProfileService

logger = logging.getLogger("job_hunting.apply_review")

REVIEW_QUEUE_STATUS = "queued"
SCREENSHOT_DIR = Path("/tmp/apply_screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


class ApplyReviewService:

    def __init__(self, db) -> None:
        self._db = db
        self._app_repo = ApplicationRepository(db)
        self._gh_repo = GitHubRepoRepository(db)

    async def prepare_application(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> dict:
        job = await self._db.get(Job, job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        from sqlalchemy import select

        result = await self._db.execute(
            select(CareerProfile).where(CareerProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        profile_dict = None
        if profile:
            profile_dict = {
                "skills": profile.skills or [],
                "years_experience": profile.years_experience or 0,
            }

        gh_svc = GitHubProfileService(self._gh_repo)
        repos = await gh_svc.get_repos(user_id)

        cover_letter = generate_cover_letter(job, repos, profile_dict)
        matched_repo = None
        from backend.services.project_matcher import match_best_repo
        best = match_best_repo(repos, job.title, job.description or "")
        if best:
            matched_repo = best.repo_name

        existing = await self._app_repo.get_by_job_and_user(job_id, user_id)
        if existing:
            app = existing
            app.status = REVIEW_QUEUE_STATUS
        else:
            app = Application(
                user_id=user_id,
                job_id=job_id,
                status=REVIEW_QUEUE_STATUS,
            )

        app.cover_letter_text = cover_letter
        app.matched_github_repo = matched_repo
        app.is_auto_generated = True

        if existing:
            await self._db.flush()
        else:
            app = await self._app_repo.create(app)

        return {
            "app_id": str(app.id),
            "job_id": str(job_id),
            "job_title": job.title,
            "company": job.company,
            "apply_url": job.apply_url,
            "cover_letter": cover_letter,
            "matched_repo": matched_repo,
            "status": REVIEW_QUEUE_STATUS,
        }

    async def get_review_queue(self, user_id: uuid.UUID) -> list[dict]:
        apps = await self._app_repo.get_by_user(user_id, skip=0, limit=100)
        queued = [a for a in apps if a.status == REVIEW_QUEUE_STATUS and a.is_auto_generated]
        queued.sort(key=lambda a: a.updated_at or a.created_at, reverse=True)

        result = []
        for app in queued:
            job = await self._db.get(Job, app.job_id) if app.job_id else None
            result.append({
                "app_id": str(app.id),
                "job_id": str(app.job_id) if app.job_id else None,
                "job_title": job.title if job else "Unknown",
                "company": job.company if job else "",
                "apply_url": job.apply_url if job else None,
                "cover_letter": app.cover_letter_text,
                "matched_repo": app.matched_github_repo,
                "before_screenshot": app.before_screenshot,
                "status": app.status,
                "created_at": str(app.created_at),
            })

        return result

    async def submit_application(self, user_id: uuid.UUID, app_id: uuid.UUID) -> dict:
        app = await self._app_repo.get_by_id(app_id)
        if not app or str(app.user_id) != str(user_id):
            raise ValueError("Application not found")

        job = await self._db.get(Job, app.job_id) if app.job_id else None

        if job and job.apply_url:
            try:
                screenshot_path = await self._auto_fill_form(job, app)
                app.before_screenshot = str(screenshot_path)
            except Exception:
                logger.exception("Auto-fill failed for job %s", job.id)

        app.status = "submitted"
        app.is_submitted = True
        app.applied_at = datetime.now(UTC).replace(tzinfo=None)
        await self._db.flush()

        return {
            "app_id": str(app.id),
            "job_title": job.title if job else "Unknown",
            "company": job.company if job else "",
            "status": "submitted",
            "applied_at": str(app.applied_at),
        }

    async def skip_application(self, user_id: uuid.UUID, app_id: uuid.UUID) -> dict:
        app = await self._app_repo.get_by_id(app_id)
        if not app or str(app.user_id) != str(user_id):
            raise ValueError("Application not found")

        app.status = "discovered"
        app.is_auto_generated = False
        await self._db.flush()

        return {"app_id": str(app.id), "status": "skipped"}

    async def _auto_fill_form(self, job: Job, app: Application) -> Path:
        screenshot_path = SCREENSHOT_DIR / f"before_{app.id}.png"
        return screenshot_path


async def prepare_application_bg(user_id: uuid.UUID, job_id: uuid.UUID) -> dict:
    factory = get_session_factory()
    async with factory() as db:
        try:
            svc = ApplyReviewService(db)
            result = await svc.prepare_application(user_id, job_id)
            await db.commit()
            return result
        except Exception:
            await db.rollback()
            raise
