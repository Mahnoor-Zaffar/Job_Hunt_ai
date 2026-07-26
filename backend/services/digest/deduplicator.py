import re
from backend.services.digest.models import ScoredJob


def remove_duplicates(jobs: list[ScoredJob]) -> list[ScoredJob]:
    seen_urls: set[str] = set()
    seen_co_title: set[str] = set()
    seen_co_loc_title: set[str] = set()
    seen_descs: set[str] = set()
    result: list[ScoredJob] = []
    removed_count = 0

    for sj in jobs:
        job = sj.job

        # Check 1: Same application URL
        url = (job.apply_url or job.url or "").lower().strip().rstrip("/")
        if url and url in seen_urls:
            removed_count += 1
            continue

        # Check 2: Same company + title
        co_norm = _normalize_text(job.company)
        title_norm = _normalize_text(job.title)
        co_title_key = f"{co_norm}|{title_norm}"
        if co_norm and title_norm and co_title_key in seen_co_title:
            removed_count += 1
            continue

        # Check 3: Same company + location + title
        loc_norm = _normalize_text(job.location or "")
        co_loc_title_key = f"{co_norm}|{loc_norm}|{title_norm}"
        if co_norm and loc_norm and title_norm and co_loc_title_key in seen_co_loc_title:
            removed_count += 1
            continue

        # Check 4: Nearly identical description
        desc_fp = _description_fingerprint(job.description or "")
        if desc_fp and desc_fp in seen_descs:
            removed_count += 1
            continue

        if url:
            seen_urls.add(url)
        if co_norm and title_norm:
            seen_co_title.add(co_title_key)
        if co_norm and loc_norm and title_norm:
            seen_co_loc_title.add(co_loc_title_key)
        if desc_fp:
            seen_descs.add(desc_fp)

        result.append(sj)

    return result


def _normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]", "", text)
    return text


def _description_fingerprint(description: str) -> str:
    text = description.lower().strip()
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 50:
        return ""
    return text[:200]
