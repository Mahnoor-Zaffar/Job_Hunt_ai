"""Resume API — upload, list, versions, delete, set active."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db
from backend.models.resume import Resume, ResumeVersion
from backend.repositories.resume import ResumeRepository, ResumeVersionRepository
from backend.schemas.base import BaseSchema

router = APIRouter(prefix="/resumes", tags=["resumes"])


class ResumeResponse(BaseSchema):
    id: str
    user_id: str | None = None
    name: str
    file_type: str
    parsed_text: str | None = None
    extracted_skills: list[str] | None = None
    total_experience_years: int | None = None
    is_primary: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ResumeVersionResponse(BaseSchema):
    id: str
    resume_id: str
    version_number: int
    change_summary: str | None = None
    created_at: datetime | None = None


class ResumeListResponse(BaseSchema):
    items: list[ResumeResponse]
    total: int


class ResumeCreateRequest(BaseSchema):
    name: str
    file_path: str
    file_type: str
    parsed_text: str | None = None


def _resume_to_response(r: Resume) -> ResumeResponse:
    return ResumeResponse(
        id=str(r.id),
        user_id=str(r.user_id) if r.user_id else None,
        name=r.name,
        file_type=r.file_type,
        parsed_text=r.parsed_text,
        extracted_skills=r.extracted_skills,
        total_experience_years=r.total_experience_years,
        is_primary=r.is_primary,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


def _version_to_response(v: ResumeVersion) -> ResumeVersionResponse:
    return ResumeVersionResponse(
        id=str(v.id),
        resume_id=str(v.resume_id),
        version_number=v.version_number,
        change_summary=v.change_summary,
        created_at=v.created_at,
    )


@router.get("", response_model=ResumeListResponse)
async def list_resumes(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
) -> ResumeListResponse:
    """List all resumes for a user."""
    repo = ResumeRepository(db)
    items = await repo.get_by_user(user_id)
    return ResumeListResponse(
        items=[_resume_to_response(r) for r in items],
        total=len(items),
    )


@router.post("", response_model=ResumeResponse, status_code=201)
async def create_resume(
    body: ResumeCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
) -> ResumeResponse:
    """Upload a new resume."""
    repo = ResumeRepository(db)
    resume = Resume(
        user_id=user_id,
        name=body.name,
        file_path=body.file_path,
        file_type=body.file_type,
        parsed_text=body.parsed_text,
    )
    created = await repo.create(resume)
    return _resume_to_response(created)


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    """Get a single resume."""
    repo = ResumeRepository(db)
    r = await repo.get_by_id(resume_id)
    if r is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    return _resume_to_response(r)


@router.delete("/{resume_id}", status_code=204)
async def delete_resume(
    resume_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a resume."""
    repo = ResumeRepository(db)
    r = await repo.get_by_id(resume_id)
    if r is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    await repo.delete(r)


@router.post("/{resume_id}/set-primary", response_model=ResumeResponse)
async def set_primary_resume(
    resume_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    """Set a resume as the primary/default."""
    repo = ResumeRepository(db)
    r = await repo.get_by_id(resume_id)
    if r is None:
        raise HTTPException(status_code=404, detail="Resume not found")

    user_resumes = await repo.get_by_user(r.user_id) if r.user_id else []
    for other in user_resumes:
        other.is_primary = other.id == r.id
    await db.flush()
    return _resume_to_response(r)


@router.get("/{resume_id}/versions", response_model=list[ResumeVersionResponse])
async def list_resume_versions(
    resume_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ResumeVersionResponse]:
    """List all versions of a resume."""
    repo = ResumeVersionRepository(db)
    versions = await repo.get_by_resume(resume_id)
    return [_version_to_response(v) for v in versions]
