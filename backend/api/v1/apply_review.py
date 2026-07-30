"""Apply Review API — prepare, review, submit, skip applications."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db
from backend.services.apply_review import ApplyReviewService
from backend.services.apply_scheduler import ApplyScheduler

router = APIRouter(prefix="/apply", tags=["apply"])


class PrepareRequest(BaseModel):
    job_id: uuid.UUID


class SubmitRequest(BaseModel):
    app_id: uuid.UUID


@router.post("/prepare")
async def prepare_application(
    body: PrepareRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
):
    svc = ApplyReviewService(db)
    try:
        result = await svc.prepare_application(user_id, body.job_id)
        await db.flush()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/review")
async def get_review_queue(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
):
    svc = ApplyReviewService(db)
    return await svc.get_review_queue(user_id)


@router.post("/submit")
async def submit_application(
    body: SubmitRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
):
    svc = ApplyReviewService(db)
    try:
        result = await svc.submit_application(user_id, body.app_id)
        await db.flush()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/skip")
async def skip_application(
    body: SubmitRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
):
    svc = ApplyReviewService(db)
    try:
        result = await svc.skip_application(user_id, body.app_id)
        await db.flush()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/schedule")
async def schedule_daily_applications(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
    count: int = Query(5, ge=1, le=10, description="Number of applications to prepare"),
):
    svc = ApplyScheduler(db)
    try:
        result = await svc.run(user_id, count)
        await db.flush()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
