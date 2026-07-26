from backend.models.career_profile import CareerProfile
from backend.models.job import Job
from backend.services.ranking.base_scorer import BaseScorer
from backend.services.ranking.models import FactorScore


class CompanyScorer(BaseScorer):
    name = "company_quality"
    max_score = 10.0

    async def score(self, job: Job, profile: CareerProfile) -> FactorScore:
        preferred = {c.lower() for c in (profile.preferred_companies or [])}
        company_lower = job.company.lower()

        bonus = 0.0
        if company_lower in preferred:
            bonus = 4.0
            details = {"preferred": True, "reason": "Company is in your preferred list"}
        else:
            details = {"preferred": False, "reason": "Company not in preferred list"}

        score = min(bonus + self.max_score * 0.6, self.max_score)
        return FactorScore(name=self.name, score=round(score, 1), max_score=self.max_score, details=details)
