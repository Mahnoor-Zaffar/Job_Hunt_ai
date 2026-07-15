"""Jobs API — full-text search, filtering, sorting, pagination, similar jobs."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db
from backend.models.job import Job
from backend.repositories.job import JobRepository
from backend.schemas.base import BaseSchema

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobResponse(BaseSchema):
    id: str
    title: str
    company: str
    company_url: str | None = None
    location: str
    city: str | None = None
    country: str | None = None
    is_remote: bool = False
    remote_type: str = "onsite"
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
    items: list[JobResponse]
    total: int
    page: int
    per_page: int
    pages: int


class JobSortField(BaseSchema):
    posted_at: str = "posted_at"
    created_at: str = "created_at"
    salary_min: str = "salary_min"
    company: str = "company"
    title: str = "title"


def _job_to_response(job: Job) -> JobResponse:
    return JobResponse(
        id=str(job.id),
        title=job.title,
        company=job.company,
        company_url=job.company_url,
        location=job.location,
        city=job.city,
        country=job.country,
        is_remote=job.is_remote,
        remote_type=job.remote_type,
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
    db: AsyncSession = Depends(get_db),
    title: str | None = Query(None, description="Filter by job title (partial match)"),
    company: str | None = Query(None, description="Filter by company name"),
    location: str | None = Query(None, description="Filter by location"),
    city: str | None = Query(None, description="Filter by city (Islamabad, Rawalpindi, Lahore)"),
    country: str | None = Query(None, description="Filter by country"),
    is_remote: bool | None = Query(None, description="Remote jobs only"),
    source: str | None = Query(None, description="Filter by source (rozee, remoteok, etc.)"),
    employment_type: str | None = Query(
        None, description="full_time, part_time, contract, internship, freelance"
    ),
    experience_level: str | None = Query(
        None, description="intern, junior, mid, senior, lead, executive"
    ),
    technologies: list[str] | None = Query(
        None, description="Required technologies (e.g., Python, Docker)"
    ),
    keywords: list[str] | None = Query(None, description="OR-filter title keywords (engineer, backend, python)"),
    salary_min: float | None = Query(None, description="Minimum salary"),
    salary_max: float | None = Query(None, description="Maximum salary"),
    posted_after: datetime | None = Query(None, description="Jobs posted after this date"),
    posted_before: datetime | None = Query(None, description="Jobs posted before this date"),
    status: str | None = Query("active", description="active, expired, applied, saved, archived"),
    sort_by: str | None = Query("posted_at", description="posted_at, salary_min, company, title"),
    sort_order: str | None = Query("desc", description="asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
) -> JobSearchResponse:
    """Search, filter, and sort jobs across all sources."""
    repo = JobRepository(db)
    fetch_limit = 500 if keywords else per_page
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
        salary_min=salary_min,
        salary_max=salary_max,
        status=status,
        skip=0,
        limit=fetch_limit,
    )

    if technologies:
        jobs = [
            j
            for j in jobs
            if j.skills and any(t.lower() in [s.lower() for s in j.skills] for t in technologies)
        ]

    if keywords:
        jobs = [
            j
            for j in jobs
            if any(k.lower() in j.title.lower() for k in keywords)
        ]

    if posted_after:
        jobs = [j for j in jobs if j.posted_at and j.posted_at >= posted_after]
    if posted_before:
        jobs = [j for j in jobs if j.posted_at and j.posted_at <= posted_before]

    reverse = sort_order == "asc"
    sort_map: dict[str, Any] = {
        "posted_at": lambda j: j.posted_at or datetime.min,
        "salary_min": lambda j: j.salary_min or 0,
        "company": lambda j: j.company.lower(),
        "title": lambda j: j.title.lower(),
    }
    if sort_by in sort_map:
        jobs.sort(key=sort_map[sort_by], reverse=not reverse)

    total = len(jobs)
    start = (page - 1) * per_page
    paged = jobs[start : start + per_page]
    pages = max(1, (total + per_page - 1) // per_page) if total else 1

    return JobSearchResponse(
        items=[_job_to_response(j) for j in paged],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Get a single job by ID."""
    repo = JobRepository(db)
    job = await repo.get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return _job_to_response(job)


@router.get("/{job_id}/similar", response_model=JobSearchResponse)
async def get_similar_jobs(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
) -> JobSearchResponse:
    """Find jobs similar to the given job (by title + skills)."""
    repo = JobRepository(db)
    job = await repo.get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    keywords = [w for w in job.title.lower().split() if len(w) > 2]
    similar: list[Job] = []
    for kw in keywords[:3]:
        matched = await repo.search(
            title=kw,
            status="active",
            skip=0,
            limit=30,
        )
        for m in matched:
            if m.id != job.id and m.id not in {s.id for s in similar}:
                similar.append(m)

    similar.sort(
        key=lambda j: len(
            (set(j.skills or []) & set(job.skills or [])) if j.skills and job.skills else []
        ),
        reverse=True,
    )

    start = (page - 1) * per_page
    paged = similar[start : start + per_page]

    return JobSearchResponse(
        items=[_job_to_response(j) for j in paged],
        total=len(similar),
        page=page,
        per_page=per_page,
        pages=max(1, (len(similar) + per_page - 1) // per_page),
    )


@router.patch("/{job_id}/status", response_model=JobResponse)
async def update_job_status(
    job_id: uuid.UUID,
    status: str = Query(..., description="new status"),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Update a job's status."""
    valid = {"active", "expired", "applied", "saved", "archived"}
    if status not in valid:
        raise HTTPException(status_code=422, detail=f"Invalid status: {status}")
    repo = JobRepository(db)
    job = await repo.get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    job.status = status
    await db.flush()
    return _job_to_response(job)
