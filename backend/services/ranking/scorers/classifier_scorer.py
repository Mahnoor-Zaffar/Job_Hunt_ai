from backend.models.career_profile import CareerProfile
from backend.models.job import Job
from backend.services.digest.classifier import classify_job
from backend.services.digest.config import get_config
from backend.services.digest.normalizer import normalize_job
from backend.services.ranking.base_scorer import BaseScorer
from backend.services.ranking.models import FactorScore


class ClassifierScorer(BaseScorer):
    name = "classifier_confidence"
    max_score = 10.0

    async def score(self, job: Job, profile: CareerProfile) -> FactorScore:
        raw = {
            "id": str(job.id),
            "title": job.title,
            "description": job.description or "",
            "skills": job.skills or [],
            "requirements": job.requirements or "",
            "company": job.company,
            "url": job.url,
            "source": job.source,
            "source_id": job.source_id,
            "location": job.location,
        }
        normal = normalize_job(raw)
        cfg = get_config()
        result = classify_job(normal, cfg)

        if result.confidence == "HIGH":
            score = self.max_score
        elif result.confidence == "MEDIUM":
            score = self.max_score * 0.5
        else:
            score = 0.0

        return FactorScore(
            name=self.name,
            score=round(score, 1),
            max_score=self.max_score,
            details={"confidence": result.confidence, "category": result.category, "accepted": result.accepted},
        )
