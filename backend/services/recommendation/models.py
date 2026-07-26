from dataclasses import dataclass, field

from backend.models.job import Job
from backend.services.ranking.models import FactorScore, RankedJob


@dataclass
class WhyExplanation:
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class Recommendation:
    job: Job
    score: float
    confidence: str
    label: str
    recommended_action: str
    factors: list[FactorScore] = field(default_factory=list)
    why: WhyExplanation = field(default_factory=WhyExplanation)
    pipeline_stage: str = "discovered"
    match_age_days: int = 0

    @classmethod
    def from_ranked(cls, ranked: RankedJob, why: WhyExplanation, pipeline_stage: str = "discovered") -> "Recommendation":
        return cls(
            job=ranked.job,
            score=ranked.composite_score,
            confidence=ranked.confidence,
            label=ranked.label,
            recommended_action=ranked.recommended_action,
            factors=ranked.factors,
            why=why,
            pipeline_stage=pipeline_stage,
        )
