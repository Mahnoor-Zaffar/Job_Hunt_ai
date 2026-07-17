"""Resume API — upload, list, versions, delete, set primary, parse."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.intelligence.resume import ResumeIntelligence
from backend.database.session import get_db
from backend.models.resume import Resume
from backend.repositories.resume import ResumeRepository, ResumeVersionRepository
from backend.schemas.base import BaseSchema
from backend.utils.validation import validate_file

router = APIRouter(prefix="/resumes", tags=["resumes"])
_intelligence = ResumeIntelligence()


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


class ParsedResumeResponse(BaseSchema):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    total_experience_years: int | None = None


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


@router.get("", response_model=ResumeListResponse)
async def list_resumes(
    db: AsyncSession = Depends(get_db), user_id: uuid.UUID = Query(...)
) -> ResumeListResponse:
    repo = ResumeRepository(db)
    items = await repo.get_by_user(user_id)
    return ResumeListResponse(items=[_resume_to_response(r) for r in items], total=len(items))


@router.post("", response_model=ResumeResponse, status_code=201)
async def create_resume(
    body: ResumeCreateRequest, db: AsyncSession = Depends(get_db), user_id: uuid.UUID = Query(...)
) -> ResumeResponse:
    repo = ResumeRepository(db)
    resume = Resume(
        user_id=user_id,
        name=body.name,
        file_path=body.file_path,
        file_type=body.file_type,
        parsed_text=body.parsed_text,
    )
    return _resume_to_response(await repo.create(resume))


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> ResumeResponse:
    repo = ResumeRepository(db)
    r = await repo.get_by_id(resume_id)
    if r is None:
        raise HTTPException(status_code=404)
    return _resume_to_response(r)


@router.delete("/{resume_id}", status_code=204)
async def delete_resume(resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    repo = ResumeRepository(db)
    r = await repo.get_by_id(resume_id)
    if r is None:
        raise HTTPException(status_code=404)
    await repo.delete(r)


@router.post("/{resume_id}/set-primary", response_model=ResumeResponse)
async def set_primary_resume(
    resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> ResumeResponse:
    repo = ResumeRepository(db)
    r = await repo.get_by_id(resume_id)
    if r is None:
        raise HTTPException(status_code=404)
    user_resumes = await repo.get_by_user(r.user_id) if r.user_id else []
    for other in user_resumes:
        other.is_primary = other.id == r.id
    await db.flush()
    return _resume_to_response(r)


@router.get("/{resume_id}/versions", response_model=list[ResumeVersionResponse])
async def list_versions(
    resume_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> list[ResumeVersionResponse]:
    repo = ResumeVersionRepository(db)
    versions = await repo.get_by_resume(resume_id)
    return [
        ResumeVersionResponse(
            id=str(v.id),
            resume_id=str(v.resume_id),
            version_number=v.version_number,
            change_summary=v.change_summary,
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.post("/parse", response_model=ParsedResumeResponse)
async def parse_resume(file: UploadFile = File(...)) -> ParsedResumeResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename")
    content = await file.read()
    try:
        validate_file(file.filename, content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    text = await _extract_text(content, file.filename)
    parsed = _intelligence.parse(text)
    return ParsedResumeResponse(
        full_name=parsed.full_name,
        email=parsed.email,
        phone=parsed.phone,
        location=parsed.location,
        summary=parsed.summary,
        skills=parsed.skills,
        experience=[
            {
                "title": e.title,
                "company": e.company,
                "start_date": e.start_date,
                "end_date": e.end_date,
            }
            for e in parsed.experience
        ],
        education=[
            {"degree": e.degree, "field": e.field, "school": e.school, "year": e.year}
            for e in parsed.education
        ],
        certifications=parsed.certifications,
        projects=parsed.projects,
        languages=parsed.languages,
        total_experience_years=parsed.total_experience_years,
    )


async def _extract_text(content: bytes, filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "pdf":
        try:
            import fitz

            doc = fitz.open(stream=content, filetype="pdf")
            text = "".join(page.get_text() for page in doc)
            doc.close()
            return text.strip()
        except Exception:
            pass
    if ext in ("docx", "doc"):
        try:
            from io import BytesIO

            from docx import Document

            return "\n".join(p.text for p in Document(BytesIO(content)).paragraphs)
        except Exception:
            pass
    return content.decode("utf-8", errors="ignore")
