import uuid

from backend.models.resume import Resume
from backend.repositories.resume import ResumeRepository, ResumeVersionRepository
from backend.services.base import BaseService


class ResumeService(BaseService):
    """Business logic for resume upload, parsing, and version management."""

    def __init__(
        self,
        resume_repo: ResumeRepository,
        version_repo: ResumeVersionRepository | None = None,
    ) -> None:
        super().__init__()
        self._resumes = resume_repo
        self._versions = version_repo

    async def get_user_resumes(self, user_id: uuid.UUID) -> list[Resume]:
        return await self._resumes.get_by_user(user_id)

    async def get_primary_resume(self, user_id: uuid.UUID) -> Resume | None:
        return await self._resumes.get_primary(user_id)

    async def set_primary(self, resume_id: uuid.UUID) -> Resume | None:
        resume = await self._resumes.get_by_id(resume_id)
        if resume is None:
            return None
        user_resumes = await self._resumes.get_by_user(resume.user_id) if resume.user_id else []
        for r in user_resumes:
            r.is_primary = r.id == resume_id
        await self._resumes.session.flush()
        return resume

    async def create_resume(
        self,
        user_id: uuid.UUID,
        name: str,
        file_path: str,
        file_type: str,
        *,
        parsed_text: str | None = None,
    ) -> Resume:
        resume = Resume(
            user_id=user_id,
            name=name,
            file_path=file_path,
            file_type=file_type,
            parsed_text=parsed_text,
        )
        return await self._resumes.create(resume)

    async def update_text(self, resume_id: uuid.UUID, parsed_text: str) -> Resume | None:
        resume = await self._resumes.get_by_id(resume_id)
        if resume is None:
            return None
        resume.parsed_text = parsed_text
        await self._resumes.session.flush()
        return resume
