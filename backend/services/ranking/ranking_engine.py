import logging

from backend.models.career_profile import CareerProfile
from backend.models.job import Job
from backend.services.ranking.models import RankedJob
from backend.services.ranking.scorers import REGISTRY
from backend.services.ranking.weights import load_actions, load_confidence_thresholds, load_labels

logger = logging.getLogger(__name__)


class RankingEngine:
    async def rank_jobs(self, jobs: list[Job], profile: CareerProfile) -> list[RankedJob]:
        if not jobs:
            return []

        labels = load_labels()
        actions = load_actions()
        conf_thresholds = load_confidence_thresholds()

        ranked: list[RankedJob] = []
        for job in jobs:
            factors = []
            for scorer_cls in REGISTRY:
                scorer = scorer_cls()
                try:
                    factor = await scorer.score(job, profile)
                    factors.append(factor)
                except Exception:
                    logger.exception("Scorer %s failed for job %s", scorer.name, job.id)
                    from backend.services.ranking.models import FactorScore
                    factors.append(FactorScore(name=scorer.name, score=0, max_score=scorer.max_score, details={"error": True}))

            composite = sum(f.score for f in factors)
            composite = max(0, min(100, composite))

            label = self._assign_label(composite, labels)
            action = actions.get(label, "Skip")

            confidence = self._assign_confidence(composite, conf_thresholds)

            ranked.append(RankedJob(
                job=job,
                composite_score=round(composite, 1),
                confidence=confidence,
                label=label,
                recommended_action=action,
                factors=factors,
            ))

        ranked.sort(key=lambda r: r.composite_score, reverse=True)
        return ranked

    def _assign_label(self, score: float, labels: dict[str, int]) -> str:
        best = "ignore"
        best_threshold = 0
        for label, threshold in sorted(labels.items(), key=lambda x: x[1], reverse=True):
            if score >= threshold and threshold >= best_threshold:
                best = label
                best_threshold = threshold
        return best

    def _assign_confidence(self, score: float, thresholds: dict[str, int]) -> str:
        if score >= thresholds.get("high", 75):
            return "high"
        elif score >= thresholds.get("medium", 45):
            return "medium"
        return "low"
