import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.outreach import Outreach
from backend.repositories.base import BaseRepository


class OutreachRepository(BaseRepository[Outreach]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Outreach, session)

    async def get_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> list[Outreach]:
        result = await self.session.execute(
            select(Outreach)
            .where(Outreach.user_id == user_id)
            .order_by(Outreach.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
