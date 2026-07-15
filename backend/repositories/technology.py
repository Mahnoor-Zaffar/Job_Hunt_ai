from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.technology import Technology
from backend.repositories.base import BaseRepository


class TechnologyRepository(BaseRepository[Technology]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Technology, session)

    async def get_by_name(self, name: str) -> Technology | None:
        result = await self.session.execute(select(Technology).where(Technology.name == name))
        return result.scalar_one_or_none()

    async def get_by_category(self, category: str) -> list[Technology]:
        result = await self.session.execute(
            select(Technology).where(Technology.category == category)
        )
        return list(result.scalars().all())

    async def get_or_create(self, name: str, category: str | None = None) -> Technology:
        existing = await self.get_by_name(name)
        if existing:
            return existing
        tech = Technology(name=name, category=category)
        return await self.create(tech)

    async def search_by_name(self, query: str, limit: int = 20) -> list[Technology]:
        result = await self.session.execute(
            select(Technology).where(Technology.name.ilike(f"%{query}%")).limit(limit)
        )
        return list(result.scalars().all())
