from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.job import Job
from backend.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Job, session)

    async def get_by_fingerprint(self, fingerprint: str) -> Job | None:
        result = await self.session.execute(select(Job).where(Job.fingerprint == fingerprint))
        return result.scalar_one_or_none()

    async def get_by_source_and_id(self, source: str, source_id: str) -> Job | None:
        result = await self.session.execute(
            select(Job).where(and_(Job.source == source, Job.source_id == source_id))
        )
        return result.scalar_one_or_none()

    async def get_active(self, skip: int = 0, limit: int = 50) -> list[Job]:
        result = await self.session.execute(
            select(Job)
            .where(Job.status == "active")
            .order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search(
        self,
        title: str | None = None,
        company: str | None = None,
        location: str | None = None,
        city: str | None = None,
        country: str | None = None,
        is_remote: bool | None = None,
        source: str | None = None,
        employment_type: str | None = None,
        experience_level: str | None = None,
        salary_min: float | None = None,
        salary_max: float | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Job]:
        conditions: list[Any] = []

        if title:
            conditions.append(Job.title.ilike(f"%{title}%"))
        if company:
            conditions.append(Job.company.ilike(f"%{company}%"))
        if location:
            conditions.append(Job.location.ilike(f"%{location}%"))
        if city:
            conditions.append(Job.city == city)
        if country:
            conditions.append(Job.country == country)
        if is_remote is not None:
            conditions.append(Job.is_remote == is_remote)
        if source:
            conditions.append(Job.source == source)
        if employment_type:
            conditions.append(Job.employment_type == employment_type)
        if experience_level:
            conditions.append(Job.experience_level == experience_level)
        if salary_min is not None:
            conditions.append(
                or_(
                    Job.salary_min >= salary_min,
                    Job.salary_max >= salary_min,
                )
            )
        if salary_max is not None:
            conditions.append(
                and_(
                    Job.salary_min <= salary_max,
                    Job.salary_max <= salary_max,
                )
            )
        if status:
            conditions.append(Job.status == status)

        query = select(Job)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(Job.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_active(self) -> int:
        result = await self.session.execute(
            select(func.count()).where(Job.status == "active").select_from(Job)
        )
        raw = result.scalar_one()
        return raw if raw is not None else 0

    async def mark_expired(self) -> int:
        result = await self.session.execute(
            select(Job).where(
                and_(
                    Job.expires_at < func.now(),
                    Job.status == "active",
                )
            )
        )
        expired = list(result.scalars().all())
        for job in expired:
            job.status = "expired"
        await self.session.flush()
        return len(expired)
