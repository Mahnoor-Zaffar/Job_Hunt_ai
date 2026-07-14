import logging
from datetime import datetime
from typing import Any

from backend.scrapers.ats.adapter import BaseATSAdapter
from backend.scrapers.ats.companies import CompanyConfig
from backend.scrapers.models.models import RawJob

logger = logging.getLogger("job_hunting.ats.ashby")


class AshbyAdapter(BaseATSAdapter):
    """Adapter for Ashby ATS public job board API.

    Each company's public-facing job board is served via::

        https://api.ashbyhq.com/posting-api/job-board/{api_key}
    """

    platform = "ashby"

    async def fetch(self, company: CompanyConfig) -> list[dict[str, Any]]:
        api_key = company.api_key
        if not api_key:
            logger.warning("No API key configured for Ashby company %s", company.name)
            return []

        url = f"https://api.ashbyhq.com/posting-api/job-board/{api_key}"
        try:
            data: dict[str, Any] = await self.http.get_json(url)
            jobs: list[dict[str, Any]] = data.get("jobs", [])
            return jobs
        except Exception:
            logger.exception("Failed to fetch Ashby jobs for %s", company.name)
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
                logger.exception("Failed to parse Ashby job for %s", company.name)
        return result

    def _parse_item(self, item: dict[str, Any], company: CompanyConfig) -> RawJob | None:
        title = (item.get("title") or "").strip()
        if not title:
            return None

        job_id = str(item.get("id", ""))
        apply_url = (item.get("jobUrl") or item.get("applyUrl") or "").strip()
        location_info = item.get("location", {}) or {}
        if isinstance(location_info, dict):
            location_str = location_info.get("name", "Remote")
        else:
            location_str = str(location_info) if location_info else "Remote"

        employment_type = item.get("employmentType")
        department = item.get("departmentName")
        description = (item.get("descriptionHtml") or item.get("descriptionPlain") or "").strip()
        team = item.get("team")

        posted_str = item.get("publishedAt", "")
        posted_at = _parse_ashby_datetime(posted_str)

        compensation = item.get("compensation", {}) or {}
        salary_min, salary_max, currency = _extract_compensation(compensation)

        return RawJob(
            title=title,
            company=company.name,
            company_url=company.careers_url,
            location=location_str,
            description=description,
            url=apply_url,
            apply_url=apply_url,
            source="ashby",
            source_id=f"ashby-{company.name}-{job_id}",
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            employment_type=employment_type,
            experience_level=team or department,
            posted_at=posted_at,
            is_remote=_is_remote(location_str),
            remote_type="remote" if _is_remote(location_str) else "onsite",
        )


def _parse_ashby_datetime(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _extract_compensation(
    compensation: dict[str, Any],
) -> tuple[float | None, float | None, str | None]:
    if not compensation:
        return None, None, None

    comp_summary = compensation.get("compensationTierSummary", "")
    if comp_summary:
        import re

        nums = re.findall(r"[\d]+[\d,.]*", comp_summary.replace(",", ""))
        values: list[float] = []
        for n in nums[:2]:
            try:
                values.append(float(n))
            except ValueError:
                continue
        return (
            values[0] if values else None,
            values[1] if len(values) > 1 else None,
            "USD",
        )

    return None, None, None


def _is_remote(location: str) -> bool:
    lower = location.lower()
    return any(kw in lower for kw in ("remote", "anywhere", "worldwide"))
