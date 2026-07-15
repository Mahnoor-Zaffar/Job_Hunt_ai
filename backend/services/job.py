import logging
import uuid

from backend.models.job import Job
from backend.repositories.company import CompanyRepository
from backend.repositories.job import JobRepository

logger = logging.getLogger("job_hunting.services.job")


class JobService:
    """Business logic for job discovery, filtering, and status management."""

    def __init__(
        self,
        job_repo: JobRepository,
        company_repo: CompanyRepository | None = None,
    ) -> None:
        self._jobs = job_repo
        self._companies = company_repo

    async def mark_applied(self, job_id: uuid.UUID) -> Job | None:
        job = await self._jobs.get_by_id(job_id)
        if job is None:
            return None
        job.status = "applied"
        await self._jobs.session.flush()
        return job

    async def mark_saved(self, job_id: uuid.UUID) -> Job | None:
        job = await self._jobs.get_by_id(job_id)
        if job is None:
            return None
        job.status = "saved"
        await self._jobs.session.flush()
        return job

    async def mark_expired(self, job_id: uuid.UUID) -> Job | None:
        job = await self._jobs.get_by_id(job_id)
        if job is None:
            return None
        job.status = "expired"
        await self._jobs.session.flush()
        return job

    async def find_duplicates(self, fingerprint: str) -> list[Job]:
        """Return all jobs sharing the same fingerprint."""
        existing = await self._jobs.get_by_fingerprint(fingerprint)
        return [existing] if existing else []

    async def expire_old_jobs(self) -> int:
        """Mark all expired jobs as inactive."""
        return await self._jobs.mark_expired()

    async def get_stats(self) -> dict[str, int]:
        """Return aggregate job counts by status."""
        active_count = await self._jobs.count_active()
        return {
            "active": active_count,
        }

    async def ensure_company_exists(self, company_name: str) -> None:
        """Create a Company record if one does not already exist."""
        if self._companies is not None:
            await self._companies.get_or_create(company_name)
