"""GitHub Profile API — fetch and view GitHub repos for truthful applications."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db
from backend.repositories.github_repo import GitHubRepoRepository
from backend.services.github_profile import GitHubProfileService

router = APIRouter(prefix="/profile/github", tags=["github"])


@router.post("/refresh")
async def refresh_github(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
    username: str = Query("Mahnoor-Zaffar", description="GitHub username"),
):
    repo = GitHubRepoRepository(db)
    svc = GitHubProfileService(repo)
    try:
        repos = await svc.refresh(user_id, username)
        await db.flush()
        return {
            "repos_fetched": len(repos),
            "repos": [
                {
                    "repo_name": r.repo_name,
                    "description": r.description,
                    "language": r.language,
                    "stars": r.stars,
                    "topics": r.topics,
                }
                for r in repos
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("")
async def list_github_repos(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
    limit: int = Query(50, ge=1, le=100),
):
    repo = GitHubRepoRepository(db)
    repos = await repo.get_by_user(user_id, limit=limit)
    return [
        {
            "repo_name": r.repo_name,
            "full_name": r.full_name,
            "description": r.description,
            "language": r.language,
            "topics": r.topics,
            "stars": r.stars,
            "forks": r.forks,
            "has_readme": r.readme_text is not None,
        }
        for r in repos
    ]
