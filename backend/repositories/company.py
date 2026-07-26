import uuid
from datetime import datetime

from sqlalchemy import select, func
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

    async def get_unverified(self, limit: int = 10) -> list[Company]:
        result = await self.session.execute(
            select(Company)
            .where(
                Company.is_active == True,  # noqa: E712
                (Company.hr_email == None) | (Company.hr_email_confidence < 75),  # noqa: E711
            )
            .order_by(Company.hr_email_verified_at.asc().nullsfirst())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_hr_email(
        self,
        company_id: uuid.UUID,
        email: str,
        confidence: int,
        source: str,
    ) -> Company | None:
        company = await self.get_by_id(company_id)
        if company:
            company.hr_email = email
            company.hr_email_confidence = confidence
            company.hr_email_source = source
            company.hr_email_verified_at = datetime.utcnow()
            await self.session.flush()
        return company

    async def count_verified_status(self) -> dict[str, int]:
        total_row = await self.session.execute(select(func.count(Company.id)))
        total = total_row.scalar() or 0
        verified_row = await self.session.execute(
            select(func.count(Company.id)).where(
                Company.hr_email_confidence >= 75  # noqa: E712
            )
        )
        verified = verified_row.scalar() or 0
        return {
            "total": total,
            "verified": verified,
            "unverified": total - verified,
        }
