from datetime import UTC, datetime

from backend.models.career_profile import CareerProfile
from backend.models.job import Job
from backend.services.ranking.base_scorer import BaseScorer
from backend.services.ranking.models import FactorScore


class PostedDateScorer(BaseScorer):
    name = "posted_date"
    max_score = 10.0

    async def score(self, job: Job, profile: CareerProfile) -> FactorScore:
        posted = job.posted_at or job.created_at
        if posted is None:
            return FactorScore(name=self.name, score=self.max_score * 0.5, max_score=self.max_score, details={"age_days": None, "reason": "No date available"})

        now = datetime.now(UTC)
        if isinstance(posted, datetime):
            if posted.tzinfo is None:
                posted = posted.replace(tzinfo=UTC)
            age = now - posted
        else:
            return FactorScore(name=self.name, score=self.max_score * 0.5, max_score=self.max_score, details={"age_days": None, "reason": "Invalid date type"})

        age_days = age.days + age.seconds / 86400

        if age_days <= 3:
            score = self.max_score
            tier = "hot"
        elif age_days <= 7:
            score = self.max_score * 0.8
            tier = "fresh"
        elif age_days <= 14:
            score = self.max_score * 0.5
            tier = "week_old"
        elif age_days <= 30:
            score = self.max_score * 0.3
            tier = "month_old"
        else:
            score = self.max_score * 0.1
            tier = "stale"

        return FactorScore(
            name=self.name,
            score=round(score, 1),
            max_score=self.max_score,
            details={"age_days": round(age_days, 1), "tier": tier},
        )
