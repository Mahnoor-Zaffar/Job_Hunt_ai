import re
from backend.services.digest.config import DigestConfig
from backend.services.digest.models import NormalizedJob


def find_matched_technologies(job: NormalizedJob, domain: str, config: DigestConfig) -> list[str]:
    tech_list = config.get_tech_domain(domain)
    matched: list[str] = []

    text_to_search = _build_search_text(job)

    for tech in tech_list:
        if tech in text_to_search:
            matched.append(tech)

    return matched


def find_all_technologies(job: NormalizedJob, config: DigestConfig) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for domain in config.tech_domains:
        matched = find_matched_technologies(job, domain, config)
        if matched:
            result[domain] = matched
    return result


def has_any_technology(job: NormalizedJob, config: DigestConfig, domains: list[str] | None = None) -> bool:
    check_domains = domains if domains else list(config.tech_domains.keys())
    text_to_search = _build_search_text(job)

    for domain in check_domains:
        tech_list = config.get_tech_domain(domain)
        for tech in tech_list:
            if tech in text_to_search:
                return True
    return False


def _build_search_text(job: NormalizedJob) -> str:
    parts = []
    if job.skills:
        parts.extend(job.skills)
    if job.description:
        parts.append(job.description.lower())
    if job.requirements:
        parts.append(job.requirements.lower())
    normalized = " ".join(parts)
    normalized = re.sub(r"[^a-z0-9\s/.#-]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized
