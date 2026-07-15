import logging

from backend.models.job import Job
from backend.repositories.job import JobRepository

logger = logging.getLogger("job_hunting.services.search")


class SearchService:
    """Business logic for job search with filtering and ranking.

    Designed to support future semantic search via pgvector without
    schema changes — the ``search()`` method accepts an optional
    ``embedding`` parameter that is ignored today but becomes
    meaningful once vector columns are added.
    """

    def __init__(self, job_repo: JobRepository) -> None:
        self._jobs = job_repo

    async def search(
        self,
        *,
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
        status: str | None = "active",
        technologies: list[str] | None = None,
        skip: int = 0,
        limit: int = 50,
        embedding: list[float] | None = None,
    ) -> list[Job]:
        """Search jobs with optional filters.

        The ``embedding`` parameter is reserved for future pgvector
        semantic search integration.
        """
        jobs = await self._jobs.search(
            title=title,
            company=company,
            location=location,
            city=city,
            country=country,
            is_remote=is_remote,
            source=source,
            employment_type=employment_type,
            experience_level=experience_level,
            salary_min=salary_min,
            salary_max=salary_max,
            status=status,
            skip=skip,
            limit=limit,
        )

        if technologies:
            jobs = [
                j
                for j in jobs
                if j.skills
                and any(t.lower() in [s.lower() for s in j.skills] for t in technologies)
            ]

        return jobs

    async def search_by_keyword(self, keyword: str, skip: int = 0, limit: int = 50) -> list[Job]:
        """Full-text style search across title and company."""
        return await self._jobs.search(
            title=keyword,
            company=keyword,
            skip=skip,
            limit=limit,
        )
