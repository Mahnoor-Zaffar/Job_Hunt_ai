"""LinkedIn Jobs scraper — Playwright for JS rendering, anti-detection."""

import logging
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote_plus

from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.models.models import RawJob
from backend.scrapers.registry.registry import register

logger = logging.getLogger("job_hunting.linkedin")

BASE_URL = "https://www.linkedin.com/jobs/search"
SUPPORTED_LOCATIONS = ["Islamabad", "Rawalpindi", "Lahore"]


@register("linkedin", display_name="LinkedIn Jobs", locations=["Pakistan", "Remote"], interval=60)
class LinkedInScraper(BaseScraper):
    source = "linkedin"

    async def fetch(self) -> list[str]:
        pages: list[str] = []
        for location in SUPPORTED_LOCATIONS:
            try:
                page = await self.get_page()
                url = f"{BASE_URL}?keywords=software+engineer&location={quote_plus(location)}&f_TPR=r604800"
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(5000)
                content = await page.content()
                pages.append(content)
                logger.debug("Fetched LinkedIn %s", location)
            except Exception:
                logger.exception("Failed LinkedIn %s", location)
        return pages

    async def parse(self, raw: Any) -> list[RawJob]:
        pages: list[str] = raw if isinstance(raw, list) else [str(raw)]
        from backend.scrapers.parser import parser as parse_utils

        jobs: list[RawJob] = []
        for page_html in pages:
            tree = parse_utils.from_html(page_html)
            for link in tree.css(
                "a.base-card__full-link, a[data-tracking-control-name='public_jobs_jserp-result']"
            ):
                title = link.text(strip=True) if hasattr(link, "text") else ""
                href = link.attributes.get("href", "") if hasattr(link, "attributes") else ""
                if not title or len(str(title)) < 3:
                    continue
                job_id = _extract_id(str(href))
                jobs.append(
                    RawJob(
                        title=str(title),
                        company="LinkedIn",
                        location="Pakistan",
                        url=str(href),
                        apply_url=str(href),
                        source=self.source,
                        source_id=f"li-{job_id}",
                        posted_at=datetime.now(UTC),
                    )
                )
        return jobs


def _extract_id(href: str) -> str:
    import re

    match = re.search(r"jobs/view/(\d+)", href)
    if match:
        return match.group(1)
    return href.split("?")[0].rsplit("/", 1)[-1][:20]
