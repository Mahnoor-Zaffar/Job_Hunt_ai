import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.platform import ATSPlatform
from backend.models.scrape_log import ScrapeLog
from backend.models.settings import Settings
from backend.models.watchlist import CompanyWatchlist
from backend.repositories.base import BaseRepository


class ATSPlatformRepository(BaseRepository[ATSPlatform]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ATSPlatform, session)

    async def get_by_name(self, name: str) -> ATSPlatform | None:
        result = await self.session.execute(select(ATSPlatform).where(ATSPlatform.name == name))
        return result.scalar_one_or_none()

    async def get_active_platforms(self) -> list[ATSPlatform]:
        result = await self.session.execute(
            select(ATSPlatform).where(
                ATSPlatform.is_active == True,  # noqa: E712
                ATSPlatform.supports_json_api == True,  # noqa: E712
            )
        )
        return list(result.scalars().all())


class ScrapeLogRepository(BaseRepository[ScrapeLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ScrapeLog, session)

    async def get_by_source(self, source: str, skip: int = 0, limit: int = 20) -> list[ScrapeLog]:
        result = await self.session.execute(
            select(ScrapeLog)
            .where(ScrapeLog.source == source)
            .order_by(ScrapeLog.started_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(self, limit: int = 50) -> list[ScrapeLog]:
        result = await self.session.execute(
            select(ScrapeLog).order_by(ScrapeLog.started_at.desc()).limit(limit)
        )
        return list(result.scalars().all())


class SettingsRepository(BaseRepository[Settings]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Settings, session)

    async def get_by_user_and_key(self, user_id: uuid.UUID, key: str) -> Settings | None:
        result = await self.session.execute(
            select(Settings).where(Settings.user_id == user_id, Settings.key == key)
        )
        return result.scalar_one_or_none()

    async def get_all_for_user(self, user_id: uuid.UUID) -> list[Settings]:
        result = await self.session.execute(select(Settings).where(Settings.user_id == user_id))
        return list(result.scalars().all())

    async def set_value(self, user_id: uuid.UUID, key: str, value: str) -> Settings:
        existing = await self.get_by_user_and_key(user_id, key)
        if existing:
            existing.value = value
            await self.session.flush()
            return existing
        setting = Settings(user_id=user_id, key=key, value=value)
        return await self.create(setting)

    async def get_value(
        self, user_id: uuid.UUID, key: str, default: str | None = None
    ) -> str | None:
        setting = await self.get_by_user_and_key(user_id, key)
        return setting.value if setting else default


class CompanyWatchlistRepository(BaseRepository[CompanyWatchlist]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CompanyWatchlist, session)

    async def get_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> list[CompanyWatchlist]:
        result = await self.session.execute(
            select(CompanyWatchlist)
            .where(CompanyWatchlist.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_active_for_user(self, user_id: uuid.UUID) -> list[CompanyWatchlist]:
        result = await self.session.execute(
            select(CompanyWatchlist).where(
                CompanyWatchlist.user_id == user_id,
                CompanyWatchlist.is_active == True,  # noqa: E712
                CompanyWatchlist.notify_on_new_jobs == True,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def get_by_user_and_company(
        self, user_id: uuid.UUID, company_name: str
    ) -> CompanyWatchlist | None:
        result = await self.session.execute(
            select(CompanyWatchlist).where(
                CompanyWatchlist.user_id == user_id,
                CompanyWatchlist.company_name == company_name,
            )
        )
        return result.scalar_one_or_none()
