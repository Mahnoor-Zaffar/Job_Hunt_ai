import logging
import uuid
from datetime import UTC, datetime

from backend.models.career_profile import CareerProfile
from backend.models.job import Job
from backend.repositories.application import ApplicationRepository
from backend.repositories.job import JobRepository
from backend.services.ranking.ranking_engine import RankingEngine
from backend.services.recommendation.explanation_builder import build_explanation
from backend.services.recommendation.models import Recommendation

logger = logging.getLogger(__name__)

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


class RecommendationService:
    def __init__(
        self,
        job_repo: JobRepository,
        app_repo: ApplicationRepository,
        ranking_engine: RankingEngine | None = None,
    ) -> None:
        self._job_repo = job_repo
        self._app_repo = app_repo
        self._ranking_engine = ranking_engine or RankingEngine()

    async def get_ranked(
        self,
        profile: CareerProfile,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        jobs = await self._job_repo.search(status="active", skip=0, limit=500)
        ranked = await self._ranking_engine.rank_jobs(jobs, profile)
        paged = ranked[offset: offset + limit]
        existing = await self._get_existing_pipeline(user_id)
        return [self._ranked_to_dict(r, existing) for r in paged]

    async def get_recommendations(
        self,
        profile: CareerProfile,
        user_id: uuid.UUID,
        limit: int = 20,
    ) -> list[Recommendation]:
        jobs = await self._job_repo.search(status="active", skip=0, limit=500)
        ranked = await self._ranking_engine.rank_jobs(jobs, profile)
        top = ranked[:limit]
        existing = await self._get_existing_pipeline(user_id)
        results: list[Recommendation] = []
        for r in top:
            stage = self._get_stage(r.job.id, existing)
            why = build_explanation(r, profile)
            rec = Recommendation.from_ranked(r, why, pipeline_stage=stage)
            results.append(rec)
        return results

    async def get_daily_actions(
        self,
        profile: CareerProfile,
        user_id: uuid.UUID,
    ) -> dict:
        recs = await self.get_recommendations(profile, user_id, limit=50)
        apply_today = [r for r in recs if r.recommended_action == "Apply Immediately"]
        existing = await self._get_existing_pipeline(user_id)
        due_follow_ups = await self._get_due_follow_ups(user_id)
        pipeline_stage_counts = self._count_stages(existing)
        missing_skills = self._aggregate_missing_skills(recs)
        return {
            "apply_today": [self._rec_to_dict(r) for r in apply_today[:5]],
            "apply_today_count": len(apply_today),
            "due_follow_ups": due_follow_ups,
            "pipeline_stage_counts": pipeline_stage_counts,
            "missing_skills": missing_skills[:10],
        }

    async def get_dashboard(
        self,
        profile: CareerProfile,
        user_id: uuid.UUID,
    ) -> dict:
        recs = await self.get_recommendations(profile, user_id, limit=50)
        existing = await self._get_existing_pipeline(user_id)
        apply_today = [r for r in recs if r.recommended_action == "Apply Immediately"]
        due_follow_ups = await self._get_due_follow_ups(user_id)
        pipeline_stage_counts = self._count_stages(existing)
        missing_skills = self._aggregate_missing_skills(recs)
        interviews = sum(1 for s in existing.values() if s == "interview")
        offers = sum(1 for s in existing.values() if s == "offer")
        return {
            "apply_today_count": len(apply_today),
            "best_matches": [self._rec_to_dict(r) for r in recs[:5]],
            "pipeline_stage_counts": pipeline_stage_counts,
            "follow_ups_due": len(due_follow_ups),
            "interviews_scheduled": interviews,
            "offers_received": offers,
            "missing_skills": missing_skills[:10],
        }

    async def _get_existing_pipeline(self, user_id: uuid.UUID) -> dict[uuid.UUID, str]:
        apps = await self._app_repo.get_by_user(user_id, skip=0, limit=500)
        return {app.job_id: app.status for app in apps}

    async def _get_due_follow_ups(self, user_id: uuid.UUID) -> list[dict]:
        apps = await self._app_repo.get_by_user(user_id, skip=0, limit=200)
        now = datetime.now(UTC)
        due = [
            a for a in apps
            if a.follow_up_at and a.follow_up_at <= now and a.status not in ("offer", "rejected", "withdrawn")
        ]
        return [{"app_id": str(a.id), "job_id": str(a.job_id), "status": a.status, "follow_up_at": str(a.follow_up_at)} for a in due[:10]]

    def _get_stage(self, job_id: uuid.UUID, existing: dict[uuid.UUID, str]) -> str:
        return existing.get(job_id, "discovered")

    def _count_stages(self, existing: dict[uuid.UUID, str]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for stage in PIPELINE_ORDER:
            count = sum(1 for s in existing.values() if s == stage)
            if count > 0:
                counts[stage] = count
        return counts

    def _aggregate_missing_skills(self, recs: list[Recommendation]) -> list[str]:
        all_missing: list[str] = []
        seen: set[str] = set()
        for r in recs:
            for s in r.why.missing_skills:
                sl = s.lower()
                if sl not in seen:
                    all_missing.append(s)
                    seen.add(sl)
        return all_missing

    def _ranked_to_dict(self, ranked, existing: dict[uuid.UUID, str]) -> dict:
        return {
            "score": ranked.composite_score,
            "confidence": ranked.confidence,
            "label": ranked.label,
            "recommended_action": ranked.recommended_action,
            "factors": {f.name: {"score": f.score, "max": f.max_score, "details": f.details} for f in ranked.factors},
            "pipeline_stage": self._get_stage(ranked.job.id, existing),
            "job": self._job_to_dict(ranked.job),
        }

    def _rec_to_dict(self, rec: Recommendation) -> dict:
        return {
            "score": rec.score,
            "confidence": rec.confidence,
            "label": rec.label,
            "recommended_action": rec.recommended_action,
            "factors": {f.name: {"score": f.score, "max": f.max_score, "details": f.details} for f in rec.factors},
            "why": {
                "strengths": rec.why.strengths,
                "weaknesses": rec.why.weaknesses,
                "missing_skills": rec.why.missing_skills,
                "recommendations": rec.why.recommendations,
            },
            "pipeline_stage": rec.pipeline_stage,
            "job": self._job_to_dict(rec.job),
        }

    def _job_to_dict(self, job: Job) -> dict:
        return {
            "id": str(job.id),
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "city": job.city,
            "country": job.country,
            "is_remote": job.is_remote,
            "remote_type": job.remote_type,
            "description": job.description,
            "requirements": job.requirements,
            "url": job.url,
            "apply_url": job.apply_url,
            "source": job.source,
            "salary_min": float(job.salary_min) if job.salary_min else None,
            "salary_max": float(job.salary_max) if job.salary_max else None,
            "currency": job.currency,
            "employment_type": job.employment_type,
            "experience_level": job.experience_level,
            "skills": job.skills,
            "posted_at": str(job.posted_at) if job.posted_at else None,
            "status": job.status,
        }
