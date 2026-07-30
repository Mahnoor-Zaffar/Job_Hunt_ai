"""Outreach API — generate and manage cold email campaigns."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db
from backend.repositories.career_profile import CareerProfileRepository
from backend.repositories.job import JobRepository
from backend.repositories.outreach import OutreachRepository
from backend.services.outreach.outreach_service import OutreachService

router = APIRouter(prefix="/outreach", tags=["outreach"])


class OutreachResponse(BaseModel):
    id: str
    user_id: str
    application_id: str | None
    job_id: str
    recipient_email: str
    recipient_name: str | None
    subject: str
    body: str
    status: str
    sent_at: str | None
    created_at: str


@router.post("/generate")
async def generate_outreach(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
    application_id: uuid.UUID | None = Query(None),
):
    profile_repo = CareerProfileRepository(db)
    profile = await profile_repo.get_by_user(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Create a career profile first")

    job_repo = JobRepository(db)
    job = await job_repo.get_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    repo = OutreachRepository(db)
    svc = OutreachService(repo)
    outreach = await svc.generate_email(job, profile, user_id, application_id)
    await db.flush()
    return _to_dict(outreach)


@router.post("/{outreach_id}/send")
async def send_outreach(
    outreach_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    repo = OutreachRepository(db)
    svc = OutreachService(repo)
    try:
        outreach = await svc.send(outreach_id)
        await db.flush()
        return _to_dict(outreach)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("")
async def list_outreach(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    repo = OutreachRepository(db)
    items = await repo.get_by_user(user_id, skip=offset, limit=limit)
    return [_to_dict(o) for o in items]


def _to_dict(o) -> dict:
    return {
        "id": str(o.id),
        "user_id": str(o.user_id),
        "application_id": str(o.application_id) if o.application_id else None,
        "job_id": str(o.job_id),
        "recipient_email": o.recipient_email,
        "recipient_name": o.recipient_name,
        "subject": o.subject,
        "body": o.body,
        "status": o.status,
        "sent_at": str(o.sent_at) if o.sent_at else None,
        "created_at": str(o.created_at),
    }
