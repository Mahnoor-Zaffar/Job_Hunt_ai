from backend.models.career_profile import CareerProfile
from backend.models.job import Job
from backend.services.ranking.base_scorer import BaseScorer
from backend.services.ranking.models import FactorScore


class SkillScorer(BaseScorer):
    name = "skills_overlap"
    max_score = 25.0

    async def score(self, job: Job, profile: CareerProfile) -> FactorScore:
        user_skills = {s.lower() for s in (profile.skills or [])}
        job_skills = {s.lower() for s in (job.skills or [])}

        if not job_skills:
            return FactorScore(name=self.name, score=self.max_score * 0.5, max_score=self.max_score, details={"reason": "No skills listed in job"})

        matched = list(user_skills & job_skills)
        missing = list(job_skills - user_skills)

        ratio = len(matched) / max(len(job_skills), 1)
        score = round(ratio * self.max_score, 1)
        score = min(score, self.max_score)

        return FactorScore(
            name=self.name,
            score=score,
            max_score=self.max_score,
            details={"matched": matched, "missing": missing, "ratio": round(ratio, 2)},
        )
