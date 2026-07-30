"""Seed github_repos table with Mahnoor Zaffar's real project data."""

import asyncio
import uuid

USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

REPOS = [
    {
        "repo_name": "Tayari.ai",
        "full_name": "Mahnoor-Zaffar/Tayari.ai",
        "description": "AI-powered interview platform for software engineers. Orchestrates end-to-end technical interviews with modular authentication, evaluation pipelines, and real-time AI feedback.",
        "language": "Python",
        "topics": ["fastapi", "nextjs", "postgresql", "redis", "supabase", "openai", "llm", "ai", "rag", "typescript"],
        "stars": 12,
    },
    {
        "repo_name": "Job_Hunt_ai",
        "full_name": "Mahnoor-Zaffar/Job_Hunt_ai",
        "description": "Job aggregation platform with support for multiple job boards and ATS integrations. Automated scraping framework with retries, concurrency, and deduplication.",
        "language": "Python",
        "topics": ["fastapi", "celery", "playwright", "postgresql", "openrouter", "scraping", "automation", "nextjs", "ai"],
        "stars": 8,
    },
    {
        "repo_name": "AuthKit",
        "full_name": "Mahnoor-Zaffar/AuthKit",
        "description": "Authentication toolkit built with FastAPI and JWT. Provides secure user authentication, token management, and role-based access control.",
        "language": "Python",
        "topics": ["fastapi", "jwt", "authentication", "python"],
        "stars": 5,
    },
    {
        "repo_name": "sktime",
        "full_name": "Mahnoor-Zaffar/sktime",
        "description": "Open-source contributions to sktime — a unified framework for machine learning with time series. Contributed improvements to forecasting modules.",
        "language": "Python",
        "topics": ["machine-learning", "time-series", "forecasting", "open-source", "python"],
        "stars": 3,
    },
    {
        "repo_name": "pandas",
        "full_name": "Mahnoor-Zaffar/pandas",
        "description": "Open-source contributions to pandas — the Python data analysis library. Contributed fixes and documentation improvements.",
        "language": "Python",
        "topics": ["data-analysis", "python", "open-source", "pandas"],
        "stars": 2,
    },
    {
        "repo_name": "napari",
        "full_name": "Mahnoor-Zaffar/napari",
        "description": "Open-source contributions to napari — a multi-dimensional image viewer for Python. Contributed to image processing features.",
        "language": "Python",
        "topics": ["image-processing", "python", "open-source", "visualization"],
        "stars": 2,
    },
    {
        "repo_name": "node",
        "full_name": "Mahnoor-Zaffar/node",
        "description": "Open-source contributions to Node.js. Assisted with documentation and minor fixes in the Node.js ecosystem.",
        "language": "JavaScript",
        "topics": ["javascript", "nodejs", "open-source", "runtime"],
        "stars": 1,
    },
]


async def seed():
    from backend.database.session import get_session_factory
    from backend.models.github_repo import GitHubRepo
    from sqlalchemy import delete, select

    factory = get_session_factory()
    async with factory() as db:
        await db.execute(delete(GitHubRepo).where(GitHubRepo.user_id == USER_ID))

        for rd in REPOS:
            repo = GitHubRepo(
                user_id=USER_ID,
                repo_name=rd["repo_name"],
                full_name=rd["full_name"],
                description=rd["description"],
                language=rd["language"],
                topics=rd["topics"],
                stars=rd["stars"],
                forks=0,
            )
            db.add(repo)

        await db.commit()
        print(f"Seeded {len(REPOS)} GitHub repos")


if __name__ == "__main__":
    asyncio.run(seed())
