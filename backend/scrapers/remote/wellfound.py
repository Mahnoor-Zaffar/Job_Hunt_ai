"""Wellfound (AngelList) scraper — public JSON API, no auth required."""

import logging
from typing import Any

from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.models.models import RawJob
from backend.scrapers.registry.registry import register

logger = logging.getLogger("job_hunting.wellfound")

API_URL = "https://wellfound.com/jobs"


@register("wellfound", display_name="Wellfound", locations=["Remote"], interval=30)
class WellfoundScraper(BaseScraper):
    source = "wellfound"

    async def fetch(self) -> list[dict[str, Any]]:
        try:
            data = await self.http.get_json(API_URL)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("jobs", [])
        except Exception:
            logger.exception("Wellfound fetch failed")
        return []

    async def parse(self, raw: Any) -> list[RawJob]:
        items: list[dict[str, Any]] = raw if isinstance(raw, list) else []
        jobs: list[RawJob] = []
        for item in items:
            try:
                title = (item.get("title") or "").strip()
                company_name = (
                    (item.get("company", {}) or {}).get("name", "")
                    if isinstance(item.get("company"), dict)
                    else (item.get("company") or "").strip()
                )
                if not title or not company_name:
                    continue

                job_id = str(item.get("id", ""))
                location = "Remote"
                tags: list[dict] = item.get("tags", []) or []
                skills = [
                    t.get("display_name", t.get("name", "")) for t in tags if isinstance(t, dict)
                ]

                jobs.append(
                    RawJob(
                        title=title,
                        company=str(company_name),
                        location=location,
                        description=(item.get("description") or "")[:3000],
                        url=f"https://wellfound.com/jobs/{job_id}",
                        apply_url=f"https://wellfound.com/jobs/{job_id}",
                        source=self.source,
                        source_id=f"wf-{job_id}",
                        salary_min=float(item["salary_min"]) if item.get("salary_min") else None,
                        salary_max=float(item["salary_max"]) if item.get("salary_max") else None,
                        currency=item.get("salary_currency") or "USD",
                        skills=skills if skills else None,
                        is_remote=True,
                        remote_type="remote",
                    )
                )
            except Exception:
                continue
        return jobs
