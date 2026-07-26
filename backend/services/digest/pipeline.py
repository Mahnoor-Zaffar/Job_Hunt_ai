import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from backend.services.digest.config import DigestConfig, get_config
from backend.services.digest.models import (
    NormalizedJob,
    ScoredJob,
    PipelineResult,
)
from backend.services.digest.normalizer import normalize_job
from backend.services.digest.scorer import score_job
from backend.services.digest.deduplicator import remove_duplicates
from backend.services.digest.categorizer import assign_categories
from backend.services.digest.sorter import sort_jobs
from backend.services.digest.email_generator import generate_email_html, generate_email_text

logger = logging.getLogger(__name__)


def run_pipeline(
    raw_jobs: list[Any],
    config: DigestConfig | None = None,
    max_total: int | None = None,
    min_confidence: str = "medium",
) -> PipelineResult:
    cfg = config or get_config()
    max_total = max_total or cfg.max_total

    start = time.monotonic()
    result = PipelineResult()

    step = lambda msg: logger.debug("Pipeline: %s", msg)

    # Stage 1: Normalize
    step("Normalizing jobs")
    normalized: list[NormalizedJob] = []
    for raw in raw_jobs:
        try:
            normalized.append(normalize_job(raw))
        except Exception as e:
            logger.warning("Failed to normalize job: %s", e)
    result.total_scraped = len(normalized)
    logger.info("Normalized %d jobs", len(normalized))

    # Stage 2: Age filter
    step("Filtering old jobs")
    max_age = timedelta(days=cfg.max_days_old)
    now = datetime.now(timezone.utc)
    age_filtered: list[NormalizedJob] = []
    for job in normalized:
        if job.posted_at and (now - job.posted_at) > max_age:
            continue
        age_filtered.append(job)
    logger.info("After age filter: %d jobs", len(age_filtered))

    # Stage 3: Classify / filter
    step("Classifying jobs")
    scored: list[ScoredJob] = []
    accepted_count = 0
    rejected_count = 0
    explanations: list[Any] = []
    for job in age_filtered:
        sj = score_job(job, cfg)
        explanations.append(sj.explanation)
        if _meets_confidence(sj, min_confidence):
            scored.append(sj)
            accepted_count += 1
        else:
            rejected_count += 1
    result.accepted = accepted_count
    result.rejected = rejected_count
    result.explanations = explanations
    logger.info("Classified: %d accepted, %d rejected", accepted_count, rejected_count)

    # Stage 4: Sort
    step("Sorting scored jobs")
    scored = sort_jobs(scored)

    # Stage 5: Deduplicate
    step("Removing duplicates")
    deduped = remove_duplicates(scored)
    result.duplicates_removed = len(scored) - len(deduped)
    logger.info("Duplicates removed: %d", result.duplicates_removed)

    # Stage 6: Categorize
    step("Assigning categories")
    categories = assign_categories(deduped, cfg)
    result.categories = categories

    # Apply max_total cap across categories
    total_included = sum(len(g.jobs) for g in categories)
    if total_included > max_total:
        step(f"Capping at {max_total} jobs")
        all_scored = []
        for g in categories:
            all_scored.extend(g.jobs)
        all_scored = sort_jobs(all_scored)[:max_total]
        categories = assign_categories(all_scored, cfg)
        result.categories = categories

    result.processing_duration_ms = (time.monotonic() - start) * 1000

    for g in categories:
        result.per_category_stats[g.category_key] = len(g.jobs)

    if result.total_scraped > 0:
        result.acceptance_rate = (result.accepted / result.total_scraped) * 100

    logger.info(
        "Pipeline complete: %d accepted, %d rejected, %d duplicates removed in %.1fms",
        result.accepted,
        result.rejected,
        result.duplicates_removed,
        result.processing_duration_ms,
    )

    return result


def _meets_confidence(sj: ScoredJob, min_confidence: str) -> bool:
    levels = {"high": 3, "medium": 2, "low": 1}
    min_level = levels.get(min_confidence, 2)
    job_level = levels.get(sj.confidence, 1)
    return job_level >= min_level


def _rejected_explanation(job: NormalizedJob, config: DigestConfig) -> Any:
    from backend.services.digest.models import Explanation, MatchResult
    from backend.services.digest.classifier import classify_job
    result = classify_job(job, config)
    return Explanation(
        result=_result_for_reason(result.reason),
        reason=result.reason,
        matched_title=result.matched_title,
        matched_skills=result.matched_technologies,
        score=0,
    )


def _result_for_reason(reason: str) -> MatchResult:
    from backend.services.digest.models import MatchResult
    r = reason.lower()
    if "intern" in r:
        return MatchResult.REJECTED_INTERNSHIP
    if "keyword" in r or "contains" in r:
        return MatchResult.REJECTED_KEYWORD
    if "technolog" in r:
        return MatchResult.REJECTED_TECH
    return MatchResult.REJECTED_TITLE


def generate_email(
    result: PipelineResult,
    config: DigestConfig | None = None,
) -> tuple[str, str]:
    start = time.monotonic()
    cfg = config or get_config()

    stats = {
        "total_scraped": result.total_scraped,
        "accepted": result.accepted,
        "rejected": result.rejected,
        "duplicates_removed": result.duplicates_removed,
    }

    html = generate_email_html(result.categories, cfg, stats)
    text = generate_email_text(result.categories, cfg, stats)

    result.email_generation_ms = (time.monotonic() - start) * 1000
    logger.info("Email generated in %.1fms", result.email_generation_ms)

    return html, text
