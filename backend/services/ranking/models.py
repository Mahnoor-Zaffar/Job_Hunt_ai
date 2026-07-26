from dataclasses import dataclass, field

from backend.models.job import Job


@dataclass
class FactorScore:
    name: str
    score: float
    max_score: float
    details: dict | None = None


@dataclass
class RankedJob:
    job: Job
    composite_score: float
    confidence: str
    label: str
    recommended_action: str
    factors: list[FactorScore] = field(default_factory=list)
