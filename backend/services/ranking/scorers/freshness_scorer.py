from datetime import UTC, datetime, timezone

from backend.models.career_profile import CareerProfile
from backend.models.job import Job
from backend.services.ranking.base_scorer import BaseScorer
from backend.services.ranking.models import FactorScore

_HALF_LIFE_DAYS = 14


class FreshnessScorer(BaseScorer):
    name = "freshness"
    max_score = 5.0

    async def score(self, job: Job, profile: CareerProfile) -> FactorScore:
        posted = job.posted_at or job.created_at
        if posted is None:
            return FactorScore(name=self.name, score=self.max_score * 0.5, max_score=self.max_score, details={"age_days": None, "reason": "No date available"})

        now = datetime.now(UTC)
        if isinstance(posted, datetime):
            if posted.tzinfo is None:
                posted = posted.replace(tzinfo=timezone.utc)
            age = now - posted
        else:
            return FactorScore(name=self.name, score=self.max_score * 0.5, max_score=self.max_score, details={"age_days": None, "reason": "Invalid date type"})

        age_days = age.days + age.seconds / 86400

        decay = 2 ** (-age_days / _HALF_LIFE_DAYS)
        score = round(self.max_score * decay, 1)
        score = max(0.0, min(score, self.max_score))

        return FactorScore(
            name=self.name,
            score=score,
            max_score=self.max_score,
            details={"age_days": round(age_days, 1), "decay": round(decay, 3)},
        )
