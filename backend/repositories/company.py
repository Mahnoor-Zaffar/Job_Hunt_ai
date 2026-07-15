from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.company import Company
from backend.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Company, session)

    async def get_by_name(self, name: str) -> Company | None:
        result = await self.session.execute(select(Company).where(Company.name == name))
        return result.scalar_one_or_none()

    async def get_active(self, skip: int = 0, limit: int = 50) -> list[Company]:
        result = await self.session.execute(
            select(Company)
            .where(Company.is_active == True)  # noqa: E712
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_or_create(self, name: str) -> Company:
        existing = await self.get_by_name(name)
        if existing:
            return existing
        company = Company(name=name)
        return await self.create(company)
