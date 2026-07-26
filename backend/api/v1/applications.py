"""Applications API — list, detail, status, notes, timeline, auto-apply."""

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db, get_session_factory
from backend.models.application import Application
from backend.repositories.application import ApplicationRepository
from backend.repositories.infrastructure import SettingsRepository
from backend.repositories.job import JobRepository
from backend.repositories.resume import ResumeRepository
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
    valid = {"discovered", "recommended", "resume_ready", "outreach_ready", "queued", "draft", "submitted", "under_review", "interview", "offer", "rejected", "withdrawn"}
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


# -- Auto-Apply -------------------------------------------------------------

_AUTO_APPLY_TASKS: dict[str, dict[str, Any]] = {}


class AutoApplyStatusResponse(BaseSchema):
    task_id: str
    status: str  # pending, running, success, failed
    step: str | None = None
    message: str | None = None
    screenshot_path: str | None = None
    filled_fields: int | None = None
    error: str | None = None


class AutoApplyStartResponse(BaseSchema):
    task_id: str
    status: str


@router.post("/{application_id}/auto-apply", response_model=AutoApplyStartResponse)
async def start_auto_apply(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
) -> AutoApplyStartResponse:
    """Run the automated application pipeline for a job.

    Launches a background task that:
    1. Opens the job's apply URL in a headless browser
    2. Detects the ATS platform (Greenhouse, Lever, Ashby, Workable)
    3. Generates AI-powered answers for application questions
    4. Fills the form, uploads resume, and submits
    """
    import asyncio

    from backend.automation.browser.manager import AutomationBrowser

    app_repo = ApplicationRepository(db)
    application = await app_repo.get_by_id(application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    if str(application.user_id) != str(user_id):
        raise HTTPException(status_code=403, detail="Not your application")

    task_id = f"aa_{application_id}_{uuid.uuid4().hex[:6]}"
    _AUTO_APPLY_TASKS[task_id] = {"status": "pending", "step": "initializing"}

    async def _run() -> None:
        try:
            from backend.automation.assist.engine import ApplicationEngine

            _AUTO_APPLY_TASKS[task_id]["status"] = "running"
            _AUTO_APPLY_TASKS[task_id]["step"] = "fetching job details"

            async with get_session_factory()() as session:
                job_repo = JobRepository(session)
                job = await job_repo.get_by_id(application.job_id)
                if not job or not job.apply_url:
                    _AUTO_APPLY_TASKS[task_id].update(
                        status="failed", error="No apply URL available", step="failed"
                    )
                    return

                resume_repo = ResumeRepository(session)
                resume = await resume_repo.get_primary(user_id)
                resume_path = resume.file_path if resume else ""

                settings_repo = SettingsRepository(session)
                candidate_profile = await settings_repo.get_value(user_id, "profile.summary", "")

            _AUTO_APPLY_TASKS[task_id]["step"] = "launching browser"

            browser = AutomationBrowser(headless=True)
            await browser.start()
            ctx = await browser.new_context()
            page = await browser.new_page(ctx)

            _AUTO_APPLY_TASKS[task_id]["step"] = "running application engine"

            engine = ApplicationEngine(page, job, candidate_profile=candidate_profile)
            result = await engine.run(resume_path=resume_path)

            _AUTO_APPLY_TASKS[task_id]["step"] = "saving result"
            _AUTO_APPLY_TASKS[task_id]["filled_fields"] = result.get("filled_fields", 0)

            async with get_session_factory()() as session:
                app_repo2 = ApplicationRepository(session)
                app = await app_repo2.get_by_id(application_id)
                if app and result.get("success"):
                    app.status = "submitted"
                    app.applied_at = datetime.now(UTC)
                    app.is_submitted = True
                    app.notes = f"Auto-applied via {result.get('platform', 'unknown')}"
                    _AUTO_APPLY_TASKS[task_id]["status"] = "success"
                    _AUTO_APPLY_TASKS[task_id]["message"] = f"Submitted via {result.get('platform', 'unknown')}"
                elif app:
                    app.notes = f"Auto-apply failed: {result.get('error', 'unknown')}"
                    _AUTO_APPLY_TASKS[task_id].update(
                        status="failed",
                        error=result.get("error", "Unknown error"),
                        message=result.get("error", "Application engine failed"),
                    )
                await session.commit()

            # Save screenshot path if available
            if result.get("record"):
                record = result["record"]
                if isinstance(record, dict) and record.get("screenshots"):
                    _AUTO_APPLY_TASKS[task_id]["screenshot_path"] = record["screenshots"][-1]

            await browser.close()

        except Exception as exc:
            _AUTO_APPLY_TASKS[task_id].update(
                status="failed", error=str(exc), step="error"
            )

    asyncio.create_task(_run())
    _AUTO_APPLY_TASKS[task_id]["status"] = "pending"

    return AutoApplyStartResponse(task_id=task_id, status="pending")


@router.get("/{application_id}/auto-apply/status", response_model=AutoApplyStatusResponse)
async def auto_apply_status(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> AutoApplyStatusResponse:
    """Check the status of an auto-apply task."""
    # Find the task for this application
    prefix = f"aa_{application_id}_"
    task = None
    for tid, tdata in _AUTO_APPLY_TASKS.items():
        if tid.startswith(prefix):
            task = tdata
            break

    if task is None:
        # Check if already applied
        repo = ApplicationRepository(db)
        app = await repo.get_by_id(application_id)
        if app and app.is_submitted:
            return AutoApplyStatusResponse(
                task_id="",
                status="success",
                message="Already applied",
                step="completed",
            )
        return AutoApplyStatusResponse(
            task_id="",
            status="not_found",
            step="unknown",
        )

    return AutoApplyStatusResponse(
        task_id="",
        status=task.get("status", "unknown"),
        step=task.get("step"),
        message=task.get("message"),
        error=task.get("error"),
        filled_fields=task.get("filled_fields"),
        screenshot_path=task.get("screenshot_path"),
    )
