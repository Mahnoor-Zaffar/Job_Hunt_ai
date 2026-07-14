import logging
from datetime import datetime
from typing import Any

from backend.scrapers.ats.adapter import BaseATSAdapter
from backend.scrapers.ats.companies import CompanyConfig
from backend.scrapers.models.models import RawJob

logger = logging.getLogger("job_hunting.ats.lever")


class LeverAdapter(BaseATSAdapter):
    """Adapter for Lever ATS public posting API.

    Each company's jobs are served at::

        https://api.lever.co/v0/postings/{company}

    Returns a JSON array of job postings with full metadata.
    """

    platform = "lever"

    async def fetch(self, company: CompanyConfig) -> list[dict[str, Any]]:
        from urllib.parse import urlparse

        base = company.careers_url.rstrip("/")

        parsed = urlparse(base)
        if "api.lever.co" not in parsed.netloc:
            company_slug = parsed.path.strip("/").split("/")[-1] if parsed.path else ""
            if not company_slug:
                logger.warning("Cannot determine Lever company slug from URL: %s", base)
                return []
            url = f"https://api.lever.co/v0/postings/{company_slug}"
        else:
            url = base

        try:
            data: list[dict[str, Any]] = await self.http.get_json(url)
            if isinstance(data, list):
                return data
        except Exception:
            logger.exception("Failed to fetch Lever jobs for %s", company.name)
            return []
        return []

    async def parse(
        self,
        raw: list[dict[str, Any]],
        company: CompanyConfig,
    ) -> list[RawJob]:
        result: list[RawJob] = []
        for item in raw:
            try:
                job = self._parse_item(item, company)
                if job:
                    result.append(job)
            except Exception:
                logger.exception("Failed to parse Lever job for %s", company.name)
        return result

    def _parse_item(self, item: dict[str, Any], company: CompanyConfig) -> RawJob | None:
        title = (item.get("text") or "").strip()
        if not title:
            return None

        job_id = str(item.get("id", ""))
        full_url = (item.get("hostedUrl") or item.get("applyUrl") or "").strip()
        categories = item.get("categories", {}) or {}
        location_str = categories.get("location") or item.get("location") or "Remote"

        description = _build_lever_description(item)
        employment_type = categories.get("commitment", None)
        experience_level = categories.get("team", None)

        posted_ts = item.get("createdAt")
        posted_at = datetime.fromtimestamp(int(posted_ts / 1000)) if posted_ts else None

        salary_raw = item.get("salaryRange") or {}
        salary_min: float | None = None
        salary_max: float | None = None
        if isinstance(salary_raw, dict):
            raw_min = salary_raw.get("min")
            raw_max = salary_raw.get("max")
            salary_min = float(raw_min) if isinstance(raw_min, (int, float, str)) else None
            salary_max = float(raw_max) if isinstance(raw_max, (int, float, str)) else None
        currency = (
            str(salary_raw.get("currency", "")).upper() or None
            if isinstance(salary_raw, dict)
            else None
        )

        return RawJob(
            title=title,
            company=company.name,
            company_url=company.careers_url,
            location=location_str,
            description=description,
            url=full_url,
            apply_url=full_url,
            source="lever",
            source_id=f"lever-{company.name}-{job_id}",
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            employment_type=employment_type,
            experience_level=experience_level,
            posted_at=posted_at,
            is_remote=_is_remote(location_str),
            remote_type="remote" if _is_remote(location_str) else "onsite",
        )


def _build_lever_description(item: dict[str, Any]) -> str:
    description_plain = (item.get("descriptionPlain") or "").strip()
    if description_plain:
        return description_plain

    lists = item.get("lists", []) or []
    body = (item.get("additionalPlain") or "").strip()
    parts = []
    for lst in lists:
        header = (lst.get("text") or "").strip()
        content = (lst.get("content") or "").strip()
        if header:
            parts.append(f"{header}\n{content}")
        elif content:
            parts.append(content)
    if body:
        parts.append(body)
    return "\n\n".join(parts) if parts else ""


def _is_remote(location: str) -> bool:
    lower = location.lower()
    return any(kw in lower for kw in ("remote", "anywhere", "worldwide"))
