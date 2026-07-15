"""Applications API — list, detail, status, notes, timeline."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db
from backend.models.application import Application
from backend.repositories.application import ApplicationRepository
from backend.schemas.base import BaseSchema

router = APIRouter(prefix="/applications", tags=["applications"])


class ApplicationResponse(BaseSchema):
    id: str
    user_id: str | None = None
    job_id: str
    resume_id: str | None = None
    status: str = "draft"
    applied_at: datetime | None = None
    cover_letter: str | None = None
    notes: str | None = None
    match_score: float | None = None
    interview_date: datetime | None = None
    feedback: str | None = None
    rejection_reason: str | None = None
    follow_up_at: datetime | None = None
    is_submitted: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ApplicationListResponse(BaseSchema):
    items: list[ApplicationResponse]
    total: int
    page: int
    per_page: int
    pages: int


class StatusUpdateRequest(BaseSchema):
    status: str


class NotesUpdateRequest(BaseSchema):
    notes: str


class RejectRequest(BaseSchema):
    reason: str


class InterviewScheduleRequest(BaseSchema):
    interview_date: datetime


class OfferRequest(BaseSchema):
    details: str = ""


class FollowUpRequest(BaseSchema):
    follow_up_at: datetime


class ApplicationCreateRequest(BaseSchema):
    job_id: uuid.UUID
    resume_id: uuid.UUID | None = None
    cover_letter: str | None = None


class ApplicationTimelineEntry(BaseSchema):
    status: str
    timestamp: datetime | None = None
    notes: str | None = None


def _application_to_response(a: Application) -> ApplicationResponse:
    return ApplicationResponse(
        id=str(a.id),
        user_id=str(a.user_id) if a.user_id else None,
        job_id=str(a.job_id),
        resume_id=str(a.resume_id) if a.resume_id else None,
        status=a.status,
        applied_at=a.applied_at,
        cover_letter=a.cover_letter,
        notes=a.notes,
        match_score=a.match_score,
        interview_date=a.interview_date,
        feedback=a.feedback,
        rejection_reason=a.rejection_reason,
        follow_up_at=a.follow_up_at,
        is_submitted=a.is_submitted,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


@router.get("", response_model=ApplicationListResponse)
async def list_applications(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="Filter by user"),
    status: str | None = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
) -> ApplicationListResponse:
    """List applications."""
    repo = ApplicationRepository(db)
    if status:
        items = await repo.get_by_status(status, skip=(page - 1) * per_page, limit=per_page)
    else:
        items = await repo.get_by_user(user_id, skip=(page - 1) * per_page, limit=per_page)

    return ApplicationListResponse(
        items=[_application_to_response(a) for a in items],
        total=len(items),
        page=page,
        per_page=per_page,
        pages=max(1, (len(items) + per_page - 1) // per_page),
    )


@router.post("", response_model=ApplicationResponse, status_code=201)
async def create_application(
    body: ApplicationCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
) -> ApplicationResponse:
    """Create a new application."""
    repo = ApplicationRepository(db)
    existing = await repo.get_by_job_and_user(body.job_id, user_id)
    if existing:
        return _application_to_response(existing)

    app = Application(
        user_id=user_id,
        job_id=body.job_id,
        resume_id=body.resume_id,
        cover_letter=body.cover_letter,
        status="draft",
    )
    created = await repo.create(app)
    return _application_to_response(created)


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """Get a single application."""
    repo = ApplicationRepository(db)
    app = await repo.get_by_id(application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return _application_to_response(app)


@router.patch("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: uuid.UUID,
    body: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """Update application status."""
    valid = {"draft", "submitted", "under_review", "interview", "offer", "rejected", "withdrawn"}
    if body.status not in valid:
        raise HTTPException(status_code=422, detail=f"Invalid status: {body.status}")

    repo = ApplicationRepository(db)
    app = await repo.get_by_id(application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")

    from datetime import UTC
    from datetime import datetime as dt

    app.status = body.status
    if body.status == "submitted" and not app.applied_at:
        app.applied_at = dt.now(UTC)
        app.is_submitted = True
    await db.flush()
    return _application_to_response(app)


@router.patch("/{application_id}/notes", response_model=ApplicationResponse)
async def update_application_notes(
    application_id: uuid.UUID,
    body: NotesUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """Update application notes."""
    repo = ApplicationRepository(db)
    app = await repo.get_by_id(application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    app.notes = body.notes
    await db.flush()
    return _application_to_response(app)


@router.get("/{application_id}/timeline", response_model=list[ApplicationTimelineEntry])
async def get_application_timeline(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ApplicationTimelineEntry]:
    """Get application status timeline."""
    repo = ApplicationRepository(db)
    app = await repo.get_by_id(application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return [
        ApplicationTimelineEntry(
            status=app.status,
            timestamp=app.applied_at or app.created_at,
            notes=app.notes,
        )
    ]


@router.patch("/{application_id}/reject", response_model=ApplicationResponse)
async def reject_application(
    application_id: uuid.UUID,
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """Reject an application with a reason."""
    from backend.services.application import ApplicationService

    repo = ApplicationRepository(db)
    svc = ApplicationService(repo)
    app = await svc.reject(application_id, body.reason)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return _application_to_response(app)


@router.patch("/{application_id}/interview", response_model=ApplicationResponse)
async def schedule_interview(
    application_id: uuid.UUID,
    body: InterviewScheduleRequest,
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """Schedule an interview for an application."""
    from backend.services.application import ApplicationService

    repo = ApplicationRepository(db)
    svc = ApplicationService(repo)
    app = await svc.schedule_interview(application_id, body.interview_date)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return _application_to_response(app)


@router.patch("/{application_id}/offer", response_model=ApplicationResponse)
async def record_offer(
    application_id: uuid.UUID,
    body: OfferRequest,
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """Record an offer for an application."""
    from backend.services.application import ApplicationService

    repo = ApplicationRepository(db)
    svc = ApplicationService(repo)
    app = await svc.record_offer(application_id, body.details)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return _application_to_response(app)


@router.patch("/{application_id}/follow-up", response_model=ApplicationResponse)
async def set_follow_up(
    application_id: uuid.UUID,
    body: FollowUpRequest,
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """Set a follow-up reminder date."""
    from backend.services.application import ApplicationService

    repo = ApplicationRepository(db)
    svc = ApplicationService(repo)
    app = await svc.set_follow_up(application_id, body.follow_up_at)
    if app is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return _application_to_response(app)


@router.get("/reminders/due", response_model=list[ApplicationResponse])
async def get_due_follow_ups(
    db: AsyncSession = Depends(get_db),
) -> list[ApplicationResponse]:
    """Get applications with due follow-up reminders."""
    from backend.services.application import ApplicationService

    repo = ApplicationRepository(db)
    svc = ApplicationService(repo)
    apps = await svc.get_due_follow_ups()
    return [_application_to_response(a) for a in apps]
