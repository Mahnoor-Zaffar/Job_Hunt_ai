"""BrightSpyre scraper — server-rendered HTML."""

import logging
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin

from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.models.models import RawJob
from backend.scrapers.parser import parser as parse_utils
from backend.scrapers.registry.registry import register

logger = logging.getLogger("job_hunting.brightspyre")

BASE_URL = "https://www.brightspyre.com"
SEARCH_URL = f"{BASE_URL}/jobs"
SUPPORTED_LOCATIONS = ["Islamabad", "Rawalpindi", "Lahore"]


@register(
    "brightspyre",
    display_name="BrightSpyre.com",
    locations=["Pakistan"],
    interval=30,
)
class BrightSpyreScraper(BaseScraper):
    source = "brightspyre"
    _MAX_PAGES = 3

    async def fetch(self) -> list[str]:
        pages: list[str] = []
        for location in SUPPORTED_LOCATIONS:
            for page in range(1, self._MAX_PAGES + 1):
                url = f"{SEARCH_URL}?location={location}&page={page}"
                try:
                    html = await self.http.get(url)
                    pages.append(html)
                    logger.debug("Fetched %s page %d", location, page)
                except Exception:
                    logger.exception("Failed %s page %d", location, page)
                    if page == 1:
                        raise
                    break
        return pages

    async def parse(self, raw: Any) -> list[RawJob]:
        pages: list[str] = raw if isinstance(raw, list) else [str(raw)]
        jobs: list[RawJob] = []

        for page_html in pages:
            tree = parse_utils.from_html(page_html)

            for link in tree.css("a.title-job, a[class*='title-job']"):
                title = link.text(strip=True) if hasattr(link, "text") else ""
                if not title:
                    continue

                href = link.attributes.get("href", "") if hasattr(link, "attributes") else ""
                full_url = urljoin(BASE_URL, str(href)) if href else ""

                source_id = _make_source_id(str(href)) if href else f"bs-{title[:20]}"

                jobs.append(
                    RawJob(
                        title=str(title),
                        company="BrightSpyre",
                        location="Pakistan",
                        url=full_url or f"{BASE_URL}/job",
                        apply_url=full_url or None,
                        source=self.source,
                        source_id=source_id,
                        posted_at=datetime.now(UTC),
                    )
                )

        return jobs


def _make_source_id(href: str) -> str:
    parts = href.rstrip("/").rsplit("/", 1)
    if len(parts) == 2 and parts[1]:
        return f"bs-{parts[1][:20]}"
    return f"bs-{href[:20]}"
