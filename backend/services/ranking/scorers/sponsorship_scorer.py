import re

from backend.models.career_profile import CareerProfile
from backend.models.job import Job
from backend.services.ranking.base_scorer import BaseScorer
from backend.services.ranking.models import FactorScore

_SPONSOR_KEYWORDS = [
    "visa sponsorship", "sponsor visa", "h1b", "h-1b", "h1-b",
    "work visa", "visa support", "visa transfer", "green card",
    "work permit", "relocation assistance", "relocation package",
    "relocation support", "visa offered",
]

_SPONSOR_NEGATIVE = [
    "no visa sponsorship", "cannot sponsor", "must have work authorization",
    "must be authorized", "no sponsorship", "visa sponsorship not available",
    "work authorization required", "us citizen", "us permanent resident",
    "unable to sponsor", "will not sponsor",
]


class SponsorshipScorer(BaseScorer):
    name = "sponsorship"
    max_score = 5.0

    async def score(self, job: Job, profile: CareerProfile) -> FactorScore:
        text = f"{job.title or ''} {job.description or ''} {job.requirements or ''}".lower()

        has_negative = any(re.search(neg, text) for neg in _SPONSOR_NEGATIVE)
        if has_negative:
            return FactorScore(name=self.name, score=0, max_score=self.max_score, details={"sponsorship": "not_available", "reason": "Job explicitly states no sponsorship"})

        has_positive = any(re.search(pos, text) for pos in _SPONSOR_KEYWORDS)
        if has_positive:
            return FactorScore(name=self.name, score=self.max_score, max_score=self.max_score, details={"sponsorship": "available", "reason": "Visa sponsorship mentioned"})

        return FactorScore(name=self.name, score=self.max_score * 0.5, max_score=self.max_score, details={"sponsorship": "unknown", "reason": "No sponsorship information found"})
