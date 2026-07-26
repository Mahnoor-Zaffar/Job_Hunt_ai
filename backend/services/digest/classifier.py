import re
from backend.services.digest.config import DigestConfig
from backend.services.digest.models import NormalizedJob, ClassificationResult, MatchResult, Explanation
from backend.services.digest.title_matcher import match_title
from backend.services.digest.deduplicator import _normalize_text


def classify_job(job: NormalizedJob, config: DigestConfig) -> ClassificationResult:
    title_explanation = match_title(job, config)

    if title_explanation.result in (
        MatchResult.REJECTED_KEYWORD,
        MatchResult.REJECTED_INTERNSHIP,
        MatchResult.REJECTED_TITLE,
    ):
        reason = title_explanation.reason
        if title_explanation.result == MatchResult.REJECTED_TITLE:
            reason = f"Title '{job.title}' does not match any supported category."
        return ClassificationResult(
            accepted=False,
            category=None,
            confidence="low",
            matched_title=title_explanation.matched_title,
            matched_technologies=[],
            reason=reason,
        )

    is_explicit = title_explanation.matched_title in config.accepted_explicit
    is_related = title_explanation.matched_title in config.accepted_related

    matched_tech: list[str] = []
    category_key: str | None = None

    if is_explicit:
        category_key = _find_category_for_title(title_explanation.matched_title, job, config)
        matched_tech = _find_tech_for_category(category_key, job, config)

        return ClassificationResult(
            accepted=True,
            category=category_key,
            confidence="high",
            matched_title=title_explanation.matched_title,
            matched_technologies=matched_tech,
            reason=f"Direct match: title '{title_explanation.matched_title}' is a recognized {_category_label(category_key, config)} role.",
        )

    if is_related:
        category_key = _find_best_category_for_generic(job, config)
        matched_tech = _find_tech_for_category(category_key, job, config)

        if not matched_tech:
            return ClassificationResult(
                accepted=False,
                category=None,
                confidence="low",
                matched_title=title_explanation.matched_title,
                matched_technologies=[],
                reason=f"Title '{title_explanation.matched_title}' is generic. Job does not contain technologies from any supported category.",
            )

        return ClassificationResult(
            accepted=True,
            category=category_key,
            confidence="medium",
            matched_title=title_explanation.matched_title,
            matched_technologies=matched_tech,
            reason=f"Generic title '{title_explanation.matched_title}' accepted because skills match {_category_label(category_key, config)}.",
        )

    return ClassificationResult(
        accepted=False,
        category=None,
        confidence="low",
        matched_title=title_explanation.matched_title,
        matched_technologies=[],
        reason=f"Title '{job.title}' did not match any accepted pattern.",
    )


def _find_category_for_title(
    matched_title: str, job: NormalizedJob, config: DigestConfig
) -> str | None:
    candidates: list[str] = []
    for cat_key in config.category_keys():
        for pattern in config.category_title_patterns(cat_key):
            if _loose_match(matched_title, pattern):
                candidates.append(cat_key)
                break

    if not candidates:
        return _find_best_category_for_generic(job, config)

    if len(candidates) == 1:
        return candidates[0]

    return _disambiguate_categories(candidates, job, config)


def _find_best_category_for_generic(
    job: NormalizedJob, config: DigestConfig
) -> str | None:
    text = _build_text(job)
    scores: dict[str, int] = {}
    for cat_key in config.category_keys():
        count = 0
        for domain in config.category_tech_domains(cat_key):
            for tech in config.get_tech_domain(domain):
                if tech in text:
                    count += 1
        if count > 0:
            scores[cat_key] = count
    if not scores:
        return _default_category(config)
    return max(scores, key=scores.get)


def _disambiguate_categories(
    candidates: list[str], job: NormalizedJob, config: DigestConfig
) -> str:
    text = _build_text(job)
    scores: dict[str, int] = {}
    for cat_key in candidates:
        count = 0
        for domain in config.category_tech_domains(cat_key):
            for tech in config.get_tech_domain(domain):
                if tech in text:
                    count += 1
        scores[cat_key] = count
    if scores:
        return max(scores, key=scores.get)
    return candidates[0]


def _find_tech_for_category(
    category_key: str | None, job: NormalizedJob, config: DigestConfig
) -> list[str]:
    if not category_key:
        return []
    text = _build_text(job)
    matched: list[str] = []
    for domain in config.category_tech_domains(category_key):
        for tech in config.get_tech_domain(domain):
            if tech in text:
                matched.append(tech)
    return list(dict.fromkeys(matched))[:10]


def _build_text(job: NormalizedJob) -> str:
    parts = []
    if job.skills:
        parts.extend(s.lower() for s in job.skills)
    if job.description:
        parts.append(job.description.lower())
    if job.requirements:
        parts.append(job.requirements.lower())
    text = " ".join(parts)
    return re.sub(r"[^a-z0-9\s/.#-]", " ", text)


def _loose_match(title_lower: str, pattern: str) -> bool:
    norm_pattern = pattern.replace("/", " ").replace(".", " ").lower().strip()
    norm_pattern = " ".join(norm_pattern.split())
    norm_title = " ".join(title_lower.split())
    return norm_pattern in norm_title


def _category_label(category_key: str | None, config: DigestConfig) -> str:
    if not category_key:
        return "Unknown"
    return config.category_label(category_key)


def _default_category(config: DigestConfig) -> str | None:
    keys = config.category_keys()
    return keys[0] if keys else None
