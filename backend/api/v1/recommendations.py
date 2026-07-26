"""Recommendations API — ranked jobs, daily actions, dashboard data."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db
from backend.repositories.application import ApplicationRepository
from backend.repositories.career_profile import CareerProfileRepository
from backend.repositories.job import JobRepository
from backend.services.recommendation.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/ranked")
async def get_ranked_jobs(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    profile_repo = CareerProfileRepository(db)
    profile = await profile_repo.get_by_user(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Create a career profile first (Settings → Career Profile)")

    job_repo = JobRepository(db)
    app_repo = ApplicationRepository(db)
    svc = RecommendationService(job_repo, app_repo)
    return await svc.get_ranked(profile, user_id, limit=limit, offset=offset)


@router.get("/recommended")
async def get_recommended_jobs(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
    limit: int = Query(20, ge=1, le=100),
):
    profile_repo = CareerProfileRepository(db)
    profile = await profile_repo.get_by_user(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Create a career profile first (Settings → Career Profile)")

    job_repo = JobRepository(db)
    app_repo = ApplicationRepository(db)
    svc = RecommendationService(job_repo, app_repo)
    recs = await svc.get_recommendations(profile, user_id, limit=limit)

    return {
        "items": [
            {
                "score": r.score,
                "confidence": r.confidence,
                "label": r.label,
                "recommended_action": r.recommended_action,
                "factors": {f.name: {"score": f.score, "max": f.max_score, "details": f.details} for f in r.factors},
                "why": {
                    "strengths": r.why.strengths,
                    "weaknesses": r.why.weaknesses,
                    "missing_skills": r.why.missing_skills,
                    "recommendations": r.why.recommendations,
                },
                "pipeline_stage": r.pipeline_stage,
                "job": {
                    "id": str(r.job.id),
                    "title": r.job.title,
                    "company": r.job.company,
                    "location": r.job.location,
                    "is_remote": r.job.is_remote,
                    "salary_min": float(r.job.salary_min) if r.job.salary_min else None,
                    "salary_max": float(r.job.salary_max) if r.job.salary_max else None,
                    "currency": r.job.currency,
                    "skills": r.job.skills,
                    "source": r.job.source,
                    "posted_at": str(r.job.posted_at) if r.job.posted_at else None,
                    "url": r.job.url,
                    "apply_url": r.job.apply_url,
                },
            }
            for r in recs
        ],
        "total": len(recs),
    }


@router.get("/daily-actions")
async def get_daily_actions(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
):
    profile_repo = CareerProfileRepository(db)
    profile = await profile_repo.get_by_user(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Create a career profile first (Settings → Career Profile)")

    job_repo = JobRepository(db)
    app_repo = ApplicationRepository(db)
    svc = RecommendationService(job_repo, app_repo)
    return await svc.get_daily_actions(profile, user_id)


@router.get("/dashboard")
async def get_dashboard_data(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
):
    profile_repo = CareerProfileRepository(db)
    profile = await profile_repo.get_by_user(user_id)
    if profile is None:
        return {
            "apply_today_count": 0,
            "best_matches": [],
            "pipeline_stage_counts": {},
            "follow_ups_due": 0,
            "interviews_scheduled": 0,
            "offers_received": 0,
            "missing_skills": [],
            "needs_profile": True,
        }

    job_repo = JobRepository(db)
    app_repo = ApplicationRepository(db)
    svc = RecommendationService(job_repo, app_repo)
    return await svc.get_dashboard(profile, user_id)
