from backend.models.career_profile import CareerProfile
from backend.models.job import Job
from backend.services.ranking.base_scorer import BaseScorer
from backend.services.ranking.models import FactorScore


class LocationScorer(BaseScorer):
    name = "location_preference"
    max_score = 10.0

    async def score(self, job: Job, profile: CareerProfile) -> FactorScore:
        pref = profile.remote_preference or "no_preference"

        if pref == "remote" and job.is_remote:
            return FactorScore(name=self.name, score=self.max_score, max_score=self.max_score, details={"match": "perfect", "reason": "Remote job matches remote preference"})

        if pref == "remote" and not job.is_remote:
            return FactorScore(name=self.name, score=0, max_score=self.max_score, details={"match": "none", "reason": "Not remote"})

        if pref == "onsite" and not job.is_remote:
            preferred = {loc.lower() for loc in (profile.preferred_locations or [])}
            job_location = (job.city or job.location or "").lower()
            if any(p in job_location for p in preferred):
                return FactorScore(name=self.name, score=self.max_score, max_score=self.max_score, details={"match": "exact", "reason": "Location matches preference"})
            return FactorScore(name=self.name, score=self.max_score * 0.5, max_score=self.max_score, details={"match": "partial", "reason": "Onsite job, location uncertain"})

        if pref == "hybrid":
            if job.is_remote:
                return FactorScore(name=self.name, score=self.max_score, max_score=self.max_score, details={"match": "perfect", "reason": "Remote-friendly hybrid preference"})
            return FactorScore(name=self.name, score=self.max_score * 0.7, max_score=self.max_score, details={"match": "partial", "reason": "Onsite but hybrid-capable"})

        return FactorScore(name=self.name, score=self.max_score * 0.5, max_score=self.max_score, details={"match": "neutral", "reason": "No location preference set"})
