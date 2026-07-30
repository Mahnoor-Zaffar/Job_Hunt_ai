import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.github_repo import GitHubRepo
from backend.repositories.base import BaseRepository


class GitHubRepoRepository(BaseRepository[GitHubRepo]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(GitHubRepo, session)

    async def get_by_user(self, user_id: uuid.UUID, limit: int = 50) -> list[GitHubRepo]:
        result = await self.session.execute(
            select(GitHubRepo)
            .where(GitHubRepo.user_id == user_id)
            .order_by(GitHubRepo.stars.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_full_name(self, full_name: str) -> GitHubRepo | None:
        result = await self.session.execute(
            select(GitHubRepo).where(GitHubRepo.full_name == full_name)
        )
        return result.scalar_one_or_none()

    async def delete_all_for_user(self, user_id: uuid.UUID) -> int:
        result = await self.session.execute(
            delete(GitHubRepo).where(GitHubRepo.user_id == user_id)
        )
        return result.rowcount
