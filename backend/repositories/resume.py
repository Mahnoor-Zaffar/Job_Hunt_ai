import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.resume import Resume, ResumeVersion
from backend.repositories.base import BaseRepository


class ResumeRepository(BaseRepository[Resume]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Resume, session)

    async def get_by_user(self, user_id: uuid.UUID) -> list[Resume]:
        result = await self.session.execute(select(Resume).where(Resume.user_id == user_id))
        return list(result.scalars().all())

    async def get_primary(self, user_id: uuid.UUID) -> Resume | None:
        result = await self.session.execute(
            select(Resume).where(
                Resume.user_id == user_id,
                Resume.is_primary == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()


class ResumeVersionRepository(BaseRepository[ResumeVersion]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ResumeVersion, session)

    async def get_by_resume(self, resume_id: uuid.UUID) -> list[ResumeVersion]:
        result = await self.session.execute(
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == resume_id)
            .order_by(ResumeVersion.version_number.desc())
        )
        return list(result.scalars().all())

    async def get_latest_version(self, resume_id: uuid.UUID) -> ResumeVersion | None:
        result = await self.session.execute(
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == resume_id)
            .order_by(ResumeVersion.version_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
