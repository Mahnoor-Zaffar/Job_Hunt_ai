from __future__ import annotations

import logging
import uuid
from datetime import datetime

import httpx

from backend.models.github_repo import GitHubRepo
from backend.repositories.github_repo import GitHubRepoRepository
from backend.database.session import get_session_factory

logger = logging.getLogger("job_hunting.github_profile")

GITHUB_API = "https://api.github.com"
GITHUB_USERNAME = "Mahnoor-Zaffar"


class GitHubProfileService:

    def __init__(self, repo: GitHubRepoRepository) -> None:
        self._repo = repo

    async def refresh(self, user_id: uuid.UUID, username: str = GITHUB_USERNAME) -> list[GitHubRepo]:
        repos_data = await self._fetch_repos(username)
        if not repos_data:
            return []

        await self._repo.delete_all_for_user(user_id)

        saved: list[GitHubRepo] = []
        for rd in repos_data:
            readme = await self._fetch_readme(username, rd.get("name", ""))
            repo = GitHubRepo(
                user_id=user_id,
                repo_name=rd.get("name", ""),
                full_name=rd.get("full_name", ""),
                description=rd.get("description"),
                language=rd.get("language"),
                topics=rd.get("topics"),
                readme_text=readme,
                stars=rd.get("stargazers_count", 0) or 0,
                forks=rd.get("forks_count", 0) or 0,
                updated_at=datetime.now(),
            )
            await self._repo.create(repo)
            saved.append(repo)

        logger.info("Refreshed %d GitHub repos for user %s", len(saved), user_id)
        return saved

    async def get_repos(self, user_id: uuid.UUID, limit: int = 50) -> list[GitHubRepo]:
        return await self._repo.get_by_user(user_id, limit=limit)

    async def _fetch_repos(self, username: str) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(f"{GITHUB_API}/users/{username}/repos?per_page=100&sort=updated")
                if r.status_code == 200:
                    return r.json()
                logger.warning("GitHub API returned %d for user %s", r.status_code, username)
        except Exception:
            logger.exception("Failed to fetch GitHub repos for %s", username)
        return []

    async def _fetch_readme(self, username: str, repo_name: str) -> str | None:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    f"{GITHUB_API}/repos/{username}/{repo_name}/readme",
                    headers={"Accept": "application/vnd.github.v3.raw"},
                )
                if r.status_code == 200:
                    return r.text[:3000]
        except Exception:
            logger.debug("Failed to fetch README for %s/%s", username, repo_name)
        return None


async def refresh_github_profile(user_id: uuid.UUID, username: str = GITHUB_USERNAME) -> list[GitHubRepo]:
    factory = get_session_factory()
    async with factory() as db:
        try:
            repo = GitHubRepoRepository(db)
            svc = GitHubProfileService(repo)
            result = await svc.refresh(user_id, username)
            await db.commit()
            return result
        except Exception:
            await db.rollback()
            raise
