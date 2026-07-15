from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db
from backend.models.job import Job
from backend.repositories.job import JobRepository
from backend.schemas.base import BaseSchema

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobItem(BaseSchema):
    id: str
    title: str
    company: str
    company_url: str | None = None
    location: str
    city: str | None = None
    country: str | None = None
    is_remote: bool = False
    description: str | None = None
    requirements: str | None = None
    url: str
    apply_url: str | None = None
    source: str
    source_id: str
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str | None = None
    employment_type: str | None = None
    experience_level: str | None = None
    skills: list[str] | None = None
    posted_at: datetime | None = None
    expires_at: datetime | None = None
    status: str = "active"
    created_at: datetime | None = None


class JobSearchResponse(BaseSchema):
    items: list[JobItem]
    total: int
    page: int
    per_page: int
    pages: int


def _job_to_item(job: Job) -> JobItem:
    return JobItem(
        id=str(job.id),
        title=job.title,
        company=job.company,
        company_url=job.company_url,
        location=job.location,
        city=job.city,
        country=job.country,
        is_remote=job.is_remote,
        description=job.description,
        requirements=job.requirements,
        url=job.url,
        apply_url=job.apply_url,
        source=job.source,
        source_id=job.source_id,
        salary_min=float(job.salary_min) if job.salary_min else None,
        salary_max=float(job.salary_max) if job.salary_max else None,
        currency=job.currency,
        employment_type=job.employment_type,
        experience_level=job.experience_level,
        skills=job.skills,
        posted_at=job.posted_at,
        expires_at=job.expires_at,
        status=job.status,
        created_at=job.created_at,
    )


@router.get("", response_model=JobSearchResponse)
async def search_jobs(
    db: AsyncSession = Depends(get_db),  # noqa: B008
    title: str | None = Query(None, description="Filter by job title"),
    company: str | None = Query(None, description="Filter by company name"),
    location: str | None = Query(None, description="Filter by location"),
    city: str | None = Query(None, description="Filter by city"),
    country: str | None = Query(None, description="Filter by country"),
    is_remote: bool | None = Query(None, description="Filter by remote status"),
    source: str | None = Query(None, description="Filter by source"),
    employment_type: str | None = Query(None, description="Filter by employment type"),
    experience_level: str | None = Query(None, description="Filter by experience level"),
    status: str | None = Query("active", description="Filter by job status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
) -> JobSearchResponse:
    """Search and filter jobs from all sources."""
    repo = JobRepository(db)

    jobs = await repo.search(
        title=title,
        company=company,
        location=location,
        city=city,
        country=country,
        is_remote=is_remote,
        source=source,
        employment_type=employment_type,
        experience_level=experience_level,
        status=status,
        skip=(page - 1) * per_page,
        limit=per_page,
    )

    total = await repo.count_active()

    items = [_job_to_item(j) for j in jobs]
    pages = max(1, (total + per_page - 1) // per_page) if total else 1

    return JobSearchResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )
