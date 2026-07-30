from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from backend.models.career_profile import CareerProfile
from backend.models.job import Job
from backend.models.outreach import Outreach
from backend.notifications.email import EmailNotifier
from backend.repositories.outreach import OutreachRepository

if TYPE_CHECKING:
    from backend.models.application import Application

logger = logging.getLogger(__name__)


class OutreachService:
    def __init__(self, repo: OutreachRepository) -> None:
        self._repo = repo
        self._notifier = EmailNotifier()

    @classmethod
    async def auto_generate_for_application(
        cls, app: Application, user_id: uuid.UUID
    ) -> None:
        from sqlalchemy import select

        from backend.database.session import get_session_factory
        from backend.models.career_profile import CareerProfile
        from backend.models.job import Job
        from backend.repositories.outreach import OutreachRepository

        factory = get_session_factory()
        async with factory() as db:
            try:
                outreach_repo = OutreachRepository(db)
                svc = cls(outreach_repo)
                job = await db.get(Job, app.job_id)
                if not job:
                    await db.rollback()
                    return
                result = await db.execute(
                    select(CareerProfile).where(CareerProfile.user_id == user_id)
                )
                profile = result.scalar_one_or_none()
                if not profile:
                    await db.rollback()
                    return
                existing = await outreach_repo.get_by_application(app.id)
                if existing:
                    await db.rollback()
                    return
                await svc.generate_email(job, profile, user_id, app.id)
                await db.commit()
            except Exception:
                await db.rollback()
                raise

    async def generate_email(
        self,
        job: Job,
        profile: CareerProfile,
        user_id: uuid.UUID,
        application_id: uuid.UUID | None = None,
    ) -> Outreach:
        recipient_email = self._guess_hr_email(job)
        recipient_name = job.company
        subject = f"Application for {job.title} position"

        body = self._build_email_body(job, profile)

        outreach = Outreach(
            user_id=user_id,
            application_id=application_id,
            job_id=job.id,
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            subject=subject,
            body=body,
            status="draft",
        )
        return await self._repo.create(outreach)

    async def send(self, outreach_id: uuid.UUID) -> Outreach:
        outreach = await self._repo.get_by_id(outreach_id)
        if outreach is None:
            raise ValueError(f"Outreach not found: {outreach_id}")

        success = await self._notifier.send(
            to=outreach.recipient_email,
            subject=outreach.subject,
            body=outreach.body,
        )
        outreach.status = "sent" if success else "failed"
        if success:
            outreach.sent_at = datetime.now(UTC)
        return outreach

    async def list_for_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> list[Outreach]:
        return await self._repo.get_by_user(user_id, skip=skip, limit=limit)

    def _guess_hr_email(self, job: Job) -> str:
        domain = ""
        if job.company_url:
            from urllib.parse import urlparse
            domain = urlparse(job.company_url).netloc
        if not domain and job.apply_url:
            from urllib.parse import urlparse
            domain = urlparse(job.apply_url).netloc
        if domain:
            return f"careers@{domain}"
        return f"hr@{job.company.lower().replace(' ', '')}.com"

    def _build_email_body(self, job: Job, profile: CareerProfile) -> str:
        name = "Hiring Team"
        role = job.title
        company = job.company
        skills_text = ", ".join((profile.skills or [])[:6])
        years = profile.years_experience or 0
        resume = (profile.resume_text or "")[:300]

        return f"""Dear {name},

I am writing to express my strong interest in the {role} position at {company}.

With {years} years of experience in software development, I have built a strong foundation in {skills_text}. My background includes designing and building scalable systems, leading technical initiatives, and collaborating across teams to deliver high-quality products.

{resume}

I am particularly drawn to {company} because of your innovative work and the opportunity to contribute to meaningful projects. I am confident that my technical expertise and passion for building great software would make me a valuable addition to your team.

I would welcome the opportunity to discuss how my experience aligns with the needs of your team. Please let me know a convenient time for a conversation.

Thank you for your time and consideration.

Best regards,
{profile.resume_text.split(chr(10))[0] if profile.resume_text else 'Applicant'}"""
