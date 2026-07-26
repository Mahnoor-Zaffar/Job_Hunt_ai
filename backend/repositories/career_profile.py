import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.career_profile import CareerProfile
from backend.repositories.base import BaseRepository


class CareerProfileRepository(BaseRepository[CareerProfile]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CareerProfile, session)

    async def get_by_user(self, user_id: uuid.UUID) -> CareerProfile | None:
        result = await self.session.execute(
            select(CareerProfile).where(CareerProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()
