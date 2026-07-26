from abc import ABC, abstractmethod

from backend.models.career_profile import CareerProfile
from backend.models.job import Job
from backend.services.ranking.models import FactorScore


class BaseScorer(ABC):
    name: str = ""
    max_score: float = 0.0

    @abstractmethod
    async def score(self, job: Job, profile: CareerProfile) -> FactorScore:
        ...
