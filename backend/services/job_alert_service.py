"""Listens to NEW_JOB_DISCOVERED events and creates alerts for watched companies.

Delivers via in-app notifications and (optionally) email.
"""

import json
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.models.notification import Notification
from backend.notifications.email import EmailNotifier
from backend.repositories.infrastructure import CompanyWatchlistRepository, SettingsRepository
from backend.repositories.job import JobRepository
from backend.repositories.notification import NotificationRepository

logger = logging.getLogger("job_hunting.job_alerts")

TECH_TITLE_KEYWORDS = {
    "developer", "engineer", "architect", "intern", "associate",
    "staff", "lead", "senior", "principal", "dev", "programmer",
    "analyst", "specialist", "consultant", "sde", "swe",
}

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class JobAlertService:
    """Matches new jobs against user watchlists and user skills, creates notifications."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = session_factory
        self._email = EmailNotifier()

    async def handle_new_job(self, event) -> None:
        """Subscribed to NEW_JOB_DISCOVERED. Processes new jobs from the event."""
        source = event.data.get("source", "")
        new_count = event.data.get("new_count", 0)
        if new_count <= 0:
            return

        async with self._factory() as session:
            job_repo = JobRepository(session)
            jobs = await job_repo.get_recent_by_source(source, limit=new_count)

        for job in jobs:
            try:
                await self._process_job(job)
            except Exception:
                logger.exception("Error processing job alert for %s", job.id)

    async def _process_job(self, job) -> None:
        """Create alerts for a new job.

        - `job_match`: any job matching user skills (no watchlist required)
        - `company_hiring` (only if company is watched)
        - email if configured
        """
        async with self._factory() as session:
            settings_repo = SettingsRepository(session)
            skills_str = await settings_repo.get_value(USER_ID, "alert.skills", "")
            min_score_str = await settings_repo.get_value(USER_ID, "alert.min_score", "0.3")
            user_email = await settings_repo.get_value(USER_ID, "alert.email", "")
            email_enabled_str = await settings_repo.get_value(USER_ID, "notifications.email", "false")
            send_email = email_enabled_str == "true" and bool(user_email)

            watch_repo = CompanyWatchlistRepository(session)
            watch = await watch_repo.get_by_user_and_company(USER_ID, job.company)

        user_skills = {s.strip().lower() for s in skills_str.split(",") if s.strip()}
        min_score = float(min_score_str)
        score = self._calculate_match_score(job, user_skills)
        matched_skills = self._get_matched_skills(job, user_skills)

        created_alert = False

        async with self._factory() as session:
            # job_match: any job meeting the score threshold
            if score >= min_score:
                session.add(Notification(
                    user_id=USER_ID,
                    type="job_match",
                    title=f"New {job.title} at {job.company}",
                    message=f"Match score: {score:.0%}. "
                            f"Skills matched: {', '.join(matched_skills) if matched_skills else 'General tech role'}. "
                            f"Location: {job.location}.",
                    job_id=job.id,
                    metadata_json=json.dumps({
                        "score": score,
                        "company": job.company,
                        "matched_skills": list(matched_skills),
                    }),
                ))
                created_alert = True

            # company_hiring: only if the company is watched
            if watch and watch.is_active and watch.notify_on_new_jobs:
                session.add(Notification(
                    user_id=USER_ID,
                    type="company_hiring",
                    title=f"{job.company} is hiring a {job.title}",
                    message=f"{job.company} posted a new role: {job.title}. Location: {job.location}.",
                    job_id=job.id,
                    metadata_json=json.dumps({"company": job.company, "title": job.title}),
                ))
                created_alert = True

            if created_alert:
                await session.commit()

        if created_alert:
            logger.info(
                "Alert created: %s at %s (score=%.0f%%)",
                job.title, job.company, score * 100,
            )

        # Send email if configured (only for skill-matched jobs)
        if send_email and score >= min_score:
            url = job.apply_url or job.url or ""
            await self._email.send_job_alert(
                to=user_email,
                title=job.title,
                company=job.company,
                location=job.location or "",
                url=url or "#",
                skills=job.skills or [],
                salary=f"${job.salary_min} - ${job.salary_max}" if job.salary_min else None,
            )

    def _calculate_match_score(self, job, user_skills: set[str]) -> float:
        """Score = 0.3 (title base) + 0.7 * skills overlap."""
        title_lower = (job.title or "").lower()
        title_words = set(title_lower.split())

        has_tech_title = bool(title_words & TECH_TITLE_KEYWORDS)
        title_base = 0.3 if has_tech_title else 0.0

        if not user_skills:
            return title_base

        job_skills = {s.lower() for s in (job.skills or [])}
        overlaps = user_skills & job_skills

        if not job_skills and has_tech_title:
            return title_base + 0.2

        if not overlaps:
            return title_base + 0.1

        overlap_ratio = len(overlaps) / len(user_skills)
        return min(title_base + overlap_ratio * 0.7, 1.0)

    @staticmethod
    def _get_matched_skills(job, user_skills: set[str]) -> set[str]:
        job_skills = {s.lower() for s in (job.skills or [])}
        return user_skills & job_skills

    async def ensure_watchlist(self, company_name: str) -> bool:
        """Auto-add a company to the user watchlist. Returns True if newly created."""
        async with self._factory() as session:
            watch_repo = CompanyWatchlistRepository(session)
            existing = await watch_repo.get_by_user_and_company(USER_ID, company_name)
            if existing:
                return False
            from backend.models.watchlist import CompanyWatchlist

            entry = CompanyWatchlist(
                user_id=USER_ID,
                company_name=company_name,
                notify_on_new_jobs=True,
                is_active=True,
                auto_watched=True,
            )
            session.add(entry)
            await session.commit()
            return True

    async def get_watchlist(self) -> list[str]:
        """Return list of company names the user is watching."""
        async with self._factory() as session:
            watch_repo = CompanyWatchlistRepository(session)
            entries = await watch_repo.get_active_for_user(USER_ID)
            return [e.company_name for e in entries]

    async def remove_watchlist(self, company_name: str) -> bool:
        """Remove a company from the watchlist."""
        async with self._factory() as session:
            watch_repo = CompanyWatchlistRepository(session)
            existing = await watch_repo.get_by_user_and_company(USER_ID, company_name)
            if not existing:
                return False
            await session.delete(existing)
            await session.commit()
            return True
