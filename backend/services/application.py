import uuid
from datetime import UTC, datetime
from typing import ClassVar

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
        """Create a new application or return existing one."""
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
        return application

    async def update_status(self, application_id: uuid.UUID, status: str) -> Application | None:
        if status not in self.VALID_STATUSES:
            self._raise_validation(f"Invalid application status: {status}")
        application = await self._applications.get_by_id(application_id)
        if application is None:
            return None
        application.status = status
        await self._applications.session.flush()
        return application

    async def get_user_applications(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> list[Application]:
        return await self._applications.get_by_user(user_id, skip, limit)

    async def get_by_status(self, status: str, skip: int = 0, limit: int = 50) -> list[Application]:
        return await self._applications.get_by_status(status, skip, limit)

    async def get_interviews(self, user_id: uuid.UUID) -> list[Application]:
        apps = await self._applications.get_by_user(user_id, skip=0, limit=200)
        return [a for a in apps if a.status == "interview"]
