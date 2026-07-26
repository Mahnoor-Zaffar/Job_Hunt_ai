from backend.models.career_profile import CareerProfile
from backend.models.job import Job
from backend.services.ranking.base_scorer import BaseScorer
from backend.services.ranking.models import FactorScore


class ResumeScorer(BaseScorer):
    name = "resume_match"
    max_score = 35.0

    async def score(self, job: Job, profile: CareerProfile) -> FactorScore:
        if not profile.resume_text or not job.description:
            return FactorScore(name=self.name, score=0, max_score=self.max_score, details={"matched": [], "reason": "No resume or description"})

        resume_lower = profile.resume_text.lower()
        desc_lower = job.description.lower()

        words = [w for w in resume_lower.split() if len(w) > 3]
        matched = [w for w in words if w in desc_lower]
        unique_matched = list(set(matched))

        overlap = len(unique_matched) / max(len(set(words)), 1)
        score = round(overlap * self.max_score, 1)
        score = min(score, self.max_score)

        return FactorScore(
            name=self.name,
            score=score,
            max_score=self.max_score,
            details={"matched": unique_matched[:20], "overlap_pct": round(overlap * 100, 1)},
        )
