"""Pipeline API — manage job opportunity stages through the career pipeline."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db
from backend.models.application import Application
from backend.repositories.application import ApplicationRepository
from backend.services.outreach.outreach_service import OutreachService

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

PIPELINE_ORDER = [
    "discovered",
    "recommended",
    "resume_ready",
    "outreach_ready",
    "queued",
    "draft",
    "submitted",
    "under_review",
    "interview",
    "offer",
]

PIPELINE_STAGES = frozenset([*PIPELINE_ORDER, "rejected", "withdrawn"])


class PipelineStageCount(BaseModel):
    stage: str
    count: int


class PipelineOverview(BaseModel):
    stages: list[PipelineStageCount]
    total: int


class SetStageRequest(BaseModel):
    stage: str


def _pipeline_stage_order(stage: str) -> int:
    return PIPELINE_ORDER.index(stage) if stage in PIPELINE_ORDER else 999


def _stage_side_effects(app: Application, stage: str, db: AsyncSession | None = None) -> list[str]:
    effects: list[str] = []
    now = datetime.now(UTC).replace(tzinfo=None)

    if stage == "submitted" and not app.applied_at:
        app.applied_at = now
        app.is_submitted = True
        effects.append("Applied at auto-set")
    elif stage == "under_review":
        app.follow_up_at = now + timedelta(days=7)
        effects.append("Follow-up set to 7 days")
    elif stage == "interview" and not app.interview_date:
        app.interview_date = now + timedelta(days=14)
        effects.append("Interview date auto-scheduled (14 days out)")
    elif stage == "offer":
        effects.append("Offer stage reached — prepare negotiation")

    if stage == "outreach_ready" and db is not None and app.job_id:
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            from backend.repositories.outreach import OutreachRepository
            or_task = loop.create_task(
                OutreachService(OutreachRepository(db)).auto_generate_for_application(app, app.user_id)
            )
            or_task.add_done_callback(lambda t: t.exception() or None)
            effects.append("Outreach email generation queued")
        except Exception:
            effects.append("Outreach generation skipped (background task failed)")

    return effects


@router.get("", response_model=PipelineOverview)
async def get_pipeline_overview(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
) -> PipelineOverview:
    repo = ApplicationRepository(db)
    apps = await repo.get_by_user(user_id, skip=0, limit=500)
    counts: dict[str, int] = {}
    for app in apps:
        stage = app.status if app.status in PIPELINE_STAGES else "discovered"
        counts[stage] = counts.get(stage, 0) + 1
    stages = sorted(
        [PipelineStageCount(stage=s, count=c) for s, c in counts.items()],
        key=lambda x: _pipeline_stage_order(x.stage),
    )
    return PipelineOverview(stages=stages, total=len(apps))


@router.get("/jobs")
async def get_pipeline_jobs(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
    stage: str | None = Query(None, description="Filter by pipeline stage"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    if stage and stage not in PIPELINE_STAGES:
        raise HTTPException(status_code=422, detail=f"Invalid pipeline stage: {stage}")

    from sqlalchemy import select

    from backend.models.job import Job

    repo = ApplicationRepository(db)
    apps = await repo.get_by_user(user_id, skip=0, limit=500)
    if stage:
        apps = [a for a in apps if a.status == stage]
    apps.sort(key=lambda a: a.updated_at or a.created_at, reverse=True)
    paged = apps[offset: offset + limit]

    job_ids = [a.job_id for a in paged if a.job_id]
    jobs_map: dict[str, dict] = {}
    if job_ids:
        result = await db.execute(
            select(Job.id, Job.title, Job.company, Job.location).where(Job.id.in_(job_ids))
        )
        for row in result.all():
            jobs_map[str(row.id)] = {"title": row.title, "company": row.company, "location": row.location}

    return [
        {
            "app_id": str(a.id),
            "job_id": str(a.job_id),
            "stage": a.status if a.status in PIPELINE_STAGES else "discovered",
            "match_score": a.match_score,
            "applied_at": str(a.applied_at) if a.applied_at else None,
            "interview_date": str(a.interview_date) if a.interview_date else None,
            "follow_up_at": str(a.follow_up_at) if a.follow_up_at else None,
            "notes": a.notes,
            "job": jobs_map.get(str(a.job_id), {}),
        }
        for a in paged
    ]


@router.post("/jobs/{job_id}/advance")
async def advance_pipeline_stage(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
    auto_submit: bool = Query(False, description="Trigger auto-apply when advancing to submitted"),
):
    repo = ApplicationRepository(db)
    app = await repo.get_by_job_and_user(job_id, user_id)
    if app is None:
        app = Application(user_id=user_id, job_id=job_id, status="discovered")
        app = await repo.create(app)

    current = app.status if app.status in PIPELINE_ORDER else "discovered"
    if current == "offer" or current in ("rejected", "withdrawn"):
        raise HTTPException(status_code=422, detail=f"Cannot advance from '{current}'")
    idx = PIPELINE_ORDER.index(current) if current in PIPELINE_ORDER else 0
    next_idx = min(idx + 1, len(PIPELINE_ORDER) - 1)
    next_stage = PIPELINE_ORDER[next_idx]
    app.status = next_stage

    effects = _stage_side_effects(app, next_stage, db)

    if auto_submit and next_stage == "submitted":
        effects.append("Marked for auto-apply (run from Applications page)")
        app.notes = (app.notes or "") + "\n[Auto-apply queued]"

    await db.flush()
    return {
        "app_id": str(app.id),
        "job_id": str(job_id),
        "previous_stage": current,
        "current_stage": next_stage,
        "effects": effects,
    }


@router.post("/jobs/{job_id}/stage")
async def set_pipeline_stage(
    job_id: uuid.UUID,
    body: SetStageRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
):
    if body.stage not in PIPELINE_STAGES:
        raise HTTPException(status_code=422, detail=f"Invalid pipeline stage: {body.stage}")
    repo = ApplicationRepository(db)
    app = await repo.get_by_job_and_user(job_id, user_id)
    if app is None:
        app = Application(user_id=user_id, job_id=job_id, status=body.stage)
        app = await repo.create(app)
    else:
        app.status = body.stage

    effects = _stage_side_effects(app, body.stage, db)

    await db.flush()
    return {
        "app_id": str(app.id),
        "job_id": str(job_id),
        "current_stage": body.stage,
        "effects": effects,
    }
