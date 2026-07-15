import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.application import Application
from backend.repositories.base import BaseRepository


class ApplicationRepository(BaseRepository[Application]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Application, session)

    async def get_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> list[Application]:
        result = await self.session.execute(
            select(Application)
            .where(Application.user_id == user_id)
            .order_by(Application.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_job_and_user(
        self, job_id: uuid.UUID, user_id: uuid.UUID
    ) -> Application | None:
        result = await self.session.execute(
            select(Application).where(Application.job_id == job_id, Application.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_status(self, status: str, skip: int = 0, limit: int = 50) -> list[Application]:
        result = await self.session.execute(
            select(Application)
            .where(Application.status == status)
            .order_by(Application.applied_at.desc().nullslast())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
