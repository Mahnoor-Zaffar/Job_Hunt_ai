from backend.models.career_profile import CareerProfile
from backend.models.job import Job
from backend.services.ranking.base_scorer import BaseScorer
from backend.services.ranking.models import FactorScore


class SalaryScorer(BaseScorer):
    name = "salary_attractiveness"
    max_score = 5.0

    async def score(self, job: Job, profile: CareerProfile) -> FactorScore:
        target = profile.preferred_salary_min
        if target is None or job.salary_min is None:
            return FactorScore(name=self.name, score=self.max_score * 0.5, max_score=self.max_score, details={"reason": "No salary data to compare"})

        job_salary = float(job.salary_min)
        ratio = job_salary / target if target > 0 else 0

        if ratio >= 1.2:
            score = self.max_score
            detail = "above target"
        elif ratio >= 1.0:
            score = self.max_score * 0.8
            detail = "meets target"
        elif ratio >= 0.8:
            score = self.max_score * 0.5
            detail = "below target"
        else:
            score = self.max_score * 0.2
            detail = "well below target"

        return FactorScore(
            name=self.name,
            score=round(score, 1),
            max_score=self.max_score,
            details={"job_salary": job_salary, "target": target, "ratio": round(ratio, 2), "verdict": detail},
        )
