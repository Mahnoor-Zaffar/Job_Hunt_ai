import logging
from datetime import datetime
from typing import Any

from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.models.models import RawJob
from backend.scrapers.registry.registry import register

logger = logging.getLogger("job_hunting.remoteok")

API_URL = "https://remoteok.com/api"


@register(
    "remoteok",
    display_name="Remote OK",
    locations=["Remote"],
    interval=30,
)
class RemoteOKScraper(BaseScraper):
    """Scraper for RemoteOK.com — public JSON API.

    The API returns metadata followed by job objects.  Each entry
    includes title, company, location, tags, salary, and a full
    markdown description.
    """

    source = "remoteok"

    async def fetch(self) -> list[dict[str, Any]]:
        data: list[dict[str, Any]] = await self.http.get_json(
            API_URL,
            headers={"Accept": "application/json"},
        )
        jobs = [item for item in data if isinstance(item, dict) and item.get("id")]
        logger.debug("Fetched %d jobs from RemoteOK API", len(jobs))
        return jobs

    async def parse(self, raw: Any) -> list[RawJob]:
        items: list[dict[str, Any]] = raw if isinstance(raw, list) else []
        result: list[RawJob] = []

        for item in items:
            try:
                raw_job = self._parse_item(item)
                if raw_job:
                    result.append(raw_job)
            except Exception:
                logger.exception("Failed to parse RemoteOK job %s", item.get("id"))

        return result

    def _parse_item(self, item: dict[str, Any]) -> RawJob | None:
        title = (item.get("position") or "").strip()
        company = (item.get("company") or "").strip()
        if not title or not company:
            return None

        tags: list[Any] = item.get("tags", []) or []
        location = (item.get("location") or "Remote").strip()
        apply_url = (item.get("apply_url") or item.get("url") or "").strip()
        job_id = str(item.get("id", ""))
        posted_epoch = item.get("epoch", item.get("date"))

        posted_at = datetime.fromtimestamp(int(posted_epoch)) if posted_epoch else None

        skills = [t for t in tags if isinstance(t, str)] if tags else None

        salary_min = _parse_remoteok_salary(item.get("salary_min"))
        salary_max = _parse_remoteok_salary(item.get("salary_max"))
        currency = (item.get("salary_currency") or "USD").upper()

        return RawJob(
            title=title,
            company=company,
            company_url=item.get("company_url"),
            location=location,
            description=(item.get("description") or "").strip(),
            url=(item.get("url") or apply_url or f"https://remoteok.com/{job_id}"),
            apply_url=apply_url or None,
            source=self.source,
            source_id=f"remoteok-{job_id}",
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            skills=skills,
            posted_at=posted_at,
            is_remote=True,
            remote_type="remote",
            requirements=None,
            employment_type=_tag_match(tags, {"full time", "part time", "contract"}) or None,
            experience_level=None,
        )


def _tag_match(tags: list[Any], candidates: set[str]) -> str | None:
    lower = {t.strip().lower() for t in tags if isinstance(t, str)}
    hit = lower & candidates
    return next(iter(hit), None)


def _parse_remoteok_salary(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
