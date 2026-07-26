from backend.services.digest.config import DigestConfig
from backend.services.digest.models import NormalizedJob, ScoredJob, ClassificationResult, MatchResult, Explanation
from backend.services.digest.classifier import classify_job


def score_job(job: NormalizedJob, config: DigestConfig) -> ScoredJob:
    result = classify_job(job, config)

    if not result.accepted:
        score = 0
        confidence = "low"
        explanation = Explanation(
            result=_explanation_result(result),
            reason=result.reason,
            matched_title=result.matched_title,
            matched_skills=result.matched_technologies,
            matched_category=result.category,
            score=0,
        )
    else:
        score = 100 if result.confidence == "high" else 70
        confidence = result.confidence
        explanation = Explanation(
            result=MatchResult.ACCEPTED,
            reason=result.reason,
            matched_title=result.matched_title,
            matched_skills=result.matched_technologies,
            matched_category=result.category,
            score=score,
        )

    return ScoredJob(
        job=job,
        score=score,
        confidence=confidence,
        category=result.category,
        explanation=explanation,
    )


def score_job_for_category(job: NormalizedJob, category_key: str, config: DigestConfig) -> ScoredJob:
    result = classify_job(job, config)

    force_category = category_key
    if not result.accepted or result.category is None:
        score = 0
        confidence = "low"
        explanation = Explanation(
            result=_explanation_result(result),
            reason=result.reason,
            matched_title=result.matched_title,
            matched_skills=[],
            matched_category=category_key,
            score=0,
        )
    else:
        score = 100 if result.confidence == "high" else 70
        confidence = result.confidence
        explanation = Explanation(
            result=MatchResult.ACCEPTED,
            reason=result.reason,
            matched_title=result.matched_title,
            matched_skills=result.matched_technologies,
            matched_category=category_key,
            score=score,
        )

    return ScoredJob(
        job=job,
        score=score,
        confidence=confidence,
        category=force_category,
        explanation=explanation,
    )


def _explanation_result(result: ClassificationResult) -> MatchResult:
    if "rejected" in result.reason.lower():
        if "intern" in result.reason.lower():
            return MatchResult.REJECTED_INTERNSHIP
        if "keyword" in result.reason.lower() or "contains" in result.reason.lower():
            return MatchResult.REJECTED_KEYWORD
        if "technolog" in result.reason.lower():
            return MatchResult.REJECTED_TECH
        return MatchResult.REJECTED_TITLE
    return MatchResult.ACCEPTED
