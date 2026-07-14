import logging
from datetime import datetime
from typing import Any

from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.models.models import RawJob
from backend.scrapers.registry.registry import register

logger = logging.getLogger("job_hunting.remotive")

API_URL = "https://remotive.com/api/remote-jobs"


@register(
    "remotive",
    display_name="Remotive",
    locations=["Remote"],
    interval=30,
)
class RemotiveScraper(BaseScraper):
    """Scraper for Remotive.com — public JSON API.

    The API returns paginated remote job listings with full metadata
    including title, company, location, salary, and description.
    """

    source = "remotive"

    async def fetch(self) -> list[dict[str, Any]]:
        data = await self.http.get_json(API_URL)
        jobs: list[dict[str, Any]] = data.get("jobs", data) if isinstance(data, dict) else data
        if isinstance(jobs, list):
            logger.debug("Fetched %d jobs from Remotive API", len(jobs))
            return jobs
        return []

    async def parse(self, raw: Any) -> list[RawJob]:
        items: list[dict[str, Any]] = raw if isinstance(raw, list) else []
        result: list[RawJob] = []

        for item in items:
            try:
                raw_job = self._parse_item(item)
                if raw_job:
                    result.append(raw_job)
            except Exception:
                logger.exception("Failed to parse Remotive job %s", item.get("id"))

        return result

    def _parse_item(self, item: dict[str, Any]) -> RawJob | None:
        title = (item.get("title") or "").strip()
        company_name = (item.get("company_name") or "").strip()
        if not title or not company_name:
            return None

        job_id = str(item.get("id", ""))
        location = (item.get("candidate_required_location") or "Remote").strip()
        apply_url = (item.get("url") or "").strip()
        job_type = (item.get("job_type") or "").strip()
        category = (item.get("category") or "").strip()
        tags: list[str] = [job_type, category] if job_type or category else []

        posted_str = item.get("publication_date", "")
        posted_at = _parse_iso(posted_str)

        salary = item.get("salary", "")
        salary_min, salary_max, currency = (
            _parse_remotive_salary(salary) if salary else (None, None, None)
        )

        return RawJob(
            title=title,
            company=company_name,
            company_url=item.get("company_logo_url"),
            location=location,
            description=(item.get("description") or "").strip(),
            url=apply_url or f"https://remotive.com/remote-jobs/{job_id}",
            apply_url=apply_url or None,
            source=self.source,
            source_id=f"remotive-{job_id}",
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            employment_type=job_type or None,
            skills=tags if tags else None,
            posted_at=posted_at,
            is_remote=True,
            remote_type="remote",
            requirements=None,
            experience_level=None,
        )


def _parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.replace("Z", ""), fmt)
        except ValueError:
            continue
    return None


def _parse_remotive_salary(
    salary_raw: str | list[Any] | dict[str, Any] | None,
) -> tuple[float | None, float | None, str | None]:
    if not salary_raw:
        return None, None, None
    if isinstance(salary_raw, str):
        import re

        nums = re.findall(r"[\d]+[\d,]*\.?\d*", salary_raw.replace(",", ""))
        values = []
        for n in nums[:2]:
            try:
                values.append(float(n))
            except ValueError:
                continue
        if not values:
            return None, None, None
        return (values[0], values[1] if len(values) > 1 else None, "USD")
    if isinstance(salary_raw, dict):
        raw_min = salary_raw.get("min")
        raw_max = salary_raw.get("max")
        return (
            float(raw_min) if isinstance(raw_min, (int, float, str)) else None,
            float(raw_max) if isinstance(raw_max, (int, float, str)) else None,
            str(salary_raw.get("currency", "USD")).upper(),
        )
    return None, None, None
