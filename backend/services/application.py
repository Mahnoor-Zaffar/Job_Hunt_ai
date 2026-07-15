import asyncio
import uuid
from datetime import UTC, datetime
from typing import ClassVar

from backend.events import (
    APPLICATION_STATUS_CHANGED,
    APPLICATION_SUBMITTED,
    DomainEvent,
    publish,
)
from backend.models.application import Application
from backend.repositories.application import ApplicationRepository
from backend.services.base import BaseService


class ApplicationService(BaseService):
    """Business logic for job application lifecycle management."""

    VALID_STATUSES: ClassVar[frozenset[str]] = frozenset(
        {
            "draft",
            "submitted",
            "under_review",
            "interview",
            "offer",
            "rejected",
            "withdrawn",
        }
    )

    def __init__(self, application_repo: ApplicationRepository) -> None:
        super().__init__()
        self._applications = application_repo

    async def apply(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        *,
        resume_id: uuid.UUID | None = None,
        cover_letter: str | None = None,
    ) -> Application:
        existing = await self._applications.get_by_job_and_user(job_id, user_id)
        if existing:
            return existing

        application = Application(
            user_id=user_id,
            job_id=job_id,
            resume_id=resume_id,
            cover_letter=cover_letter,
            status="draft",
        )
        return await self._applications.create(application)

    async def submit(self, application_id: uuid.UUID) -> Application | None:
        application = await self._applications.get_by_id(application_id)
        if application is None:
            return None
        application.status = "submitted"
        application.applied_at = datetime.now(UTC)
        application.is_submitted = True
        await self._applications.session.flush()

        _ = asyncio.create_task(
            publish(
                DomainEvent(
                    name=APPLICATION_SUBMITTED,
                    data={"application_id": str(application.id), "status": "submitted"},
                )
            )
        )
        return application

    async def update_status(self, application_id: uuid.UUID, status: str) -> Application | None:
        if status not in self.VALID_STATUSES:
            self._raise_validation(f"Invalid application status: {status}")
        application = await self._applications.get_by_id(application_id)
        if application is None:
            return None
        application.status = status
        await self._applications.session.flush()

        _ = asyncio.create_task(
            publish(
                DomainEvent(
                    name=APPLICATION_STATUS_CHANGED,
                    data={"application_id": str(application.id), "status": status},
                )
            )
        )
        return application

    async def reject(self, application_id: uuid.UUID, reason: str) -> Application | None:
        application = await self._applications.get_by_id(application_id)
        if application is None:
            return None
        application.status = "rejected"
        application.rejection_reason = reason
        await self._applications.session.flush()
        return application

    async def schedule_interview(
        self, application_id: uuid.UUID, interview_date: datetime
    ) -> Application | None:
        application = await self._applications.get_by_id(application_id)
        if application is None:
            return None
        application.status = "interview"
        application.interview_date = interview_date
        await self._applications.session.flush()
        return application

    async def record_offer(
        self, application_id: uuid.UUID, details: str = ""
    ) -> Application | None:
        application = await self._applications.get_by_id(application_id)
        if application is None:
            return None
        application.status = "offer"
        application.notes = f"{application.notes or ''}\n[OFFER] {details}".strip()
        await self._applications.session.flush()
        return application

    async def set_follow_up(
        self, application_id: uuid.UUID, follow_up_at: datetime
    ) -> Application | None:
        application = await self._applications.get_by_id(application_id)
        if application is None:
            return None
        application.follow_up_at = follow_up_at
        await self._applications.session.flush()
        return application

    async def get_due_follow_ups(self) -> list[Application]:
        apps = await self._applications.get_by_status("under_review", skip=0, limit=200)
        now = datetime.now(UTC)
        return [a for a in apps if a.follow_up_at and a.follow_up_at <= now]

    async def get_user_applications(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> list[Application]:
        return await self._applications.get_by_user(user_id, skip, limit)

    async def get_by_status(self, status: str, skip: int = 0, limit: int = 50) -> list[Application]:
        return await self._applications.get_by_status(status, skip, limit)

    async def get_interviews(self, user_id: uuid.UUID) -> list[Application]:
        apps = await self._applications.get_by_user(user_id, skip=0, limit=200)
        return [a for a in apps if a.status == "interview"]
