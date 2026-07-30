import re
from backend.services.digest.config import DigestConfig
from backend.services.digest.models import MatchResult, Explanation, NormalizedJob


def match_title(job: NormalizedJob, config: DigestConfig) -> Explanation:
    title_lower = job.title.lower().strip()

    if config.reject_internships and ("intern" in title_lower or "internship" in title_lower):
        return Explanation(
            result=MatchResult.REJECTED_INTERNSHIP,
            reason="Title indicates an internship position",
            matched_title=title_lower,
        )

    for pattern in config.rejected_patterns:
        if pattern in title_lower:
            return Explanation(
                result=MatchResult.REJECTED_KEYWORD,
                reason=f"Title contains rejected keyword: {pattern}",
                matched_title=pattern,
            )

    for accepted in config.accepted_explicit:
        if _title_matches(title_lower, accepted):
            return Explanation(
                result=MatchResult.ACCEPTED,
                reason=f"Matched explicit accepted title: {accepted}",
                matched_title=accepted,
            )

    for related in config.accepted_related:
        if _title_matches(title_lower, related):
            return Explanation(
                result=MatchResult.ACCEPTED,
                reason=f"Matched related title: {related} (requires tech stack validation)",
                matched_title=related,
            )

    return Explanation(
        result=MatchResult.REJECTED_TITLE,
        reason=f"Title '{job.title}' did not match any accepted title patterns",
        matched_title=title_lower,
    )


def _title_matches(title_lower: str, pattern: str) -> bool:
    norm_title = re.sub(r"[^a-z0-9\s()/]", " ", title_lower)
    norm_title = re.sub(r"\s+", " ", norm_title).strip()

    norm_pattern = re.sub(r"[^a-z0-9\s()/]", " ", pattern)
    norm_pattern = re.sub(r"\s+", " ", norm_pattern).strip()

    if norm_pattern in norm_title:
        return True

    pattern_variants = _generate_variants(norm_pattern)
    for variant in pattern_variants:
        if variant in norm_title:
            return True

    words = norm_pattern.split()
    if len(words) >= 2:
        return all(w in norm_title.split() for w in words)
    return False


def _generate_variants(pattern: str) -> list[str]:
    variants = []
    if "/" in pattern:
        parts = [p.strip() for p in pattern.split("/")]
        if len(parts) == 2:
            variants.append(f"{parts[0]} {parts[1]}")
            variants.append(f"{parts[1]} {parts[0]}")
    if "." in pattern:
        parts = pattern.split(".")
        if len(parts) >= 2:
            joined = "".join(parts)
            variants.append(joined)

    if pattern == "sre":
        variants.append("site reliability engineer")

    return variants
