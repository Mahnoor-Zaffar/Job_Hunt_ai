from backend.models.career_profile import CareerProfile
from backend.models.job import Job
from backend.services.ranking.base_scorer import BaseScorer
from backend.services.ranking.models import FactorScore


class ExperienceLevelScorer(BaseScorer):
    name = "experience_level_match"
    max_score = 10.0

    async def score(self, job: Job, profile: CareerProfile) -> FactorScore:
        user_years = profile.years_experience or 0

        if not job.experience_level and not job.requirements:
            return FactorScore(name=self.name, score=self.max_score * 0.5, max_score=self.max_score, details={"reason": "No experience level listed"})

        job_exp = (job.experience_level or "").lower()

        if "senior" in job_exp or "sr" in job_exp or "lead" in job_exp or "principal" in job_exp:
            required_years = 5
            label = "senior"
        elif "mid" in job_exp or "intermediate" in job_exp:
            required_years = 3
            label = "mid"
        elif "junior" in job_exp or "entry" in job_exp or "graduate" in job_exp or "trainee" in job_exp:
            required_years = 1
            label = "junior"
        elif "director" in job_exp or "head" in job_exp or "vp" in job_exp or "chief" in job_exp:
            required_years = 8
            label = "director"
        elif "intern" in job_exp or "internship" in job_exp:
            required_years = 0
            label = "intern"
        else:
            return FactorScore(name=self.name, score=self.max_score * 0.7, max_score=self.max_score, details={"reason": "No clear level, giving partial credit"})

        ratio = user_years / max(required_years, 1)
        if ratio >= 1.5:
            score = self.max_score
            verdict = "overqualified"
        elif ratio >= 1.0:
            score = self.max_score
            verdict = "matches"
        elif ratio >= 0.7:
            score = self.max_score * 0.7
            verdict = "slightly_under"
        elif ratio >= 0.4:
            score = self.max_score * 0.4
            verdict = "underqualified"
        else:
            score = self.max_score * 0.15
            verdict = "way_under"

        return FactorScore(
            name=self.name,
            score=round(score, 1),
            max_score=self.max_score,
            details={"required_level": label, "required_years": required_years, "user_years": user_years, "verdict": verdict},
        )
