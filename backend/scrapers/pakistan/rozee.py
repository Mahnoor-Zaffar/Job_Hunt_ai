"""Rozee.pk scraper — CloudFlare-protected, requires Playwright rendering."""

import logging
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin

from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.models.models import RawJob
from backend.scrapers.parser import parser as parse_utils
from backend.scrapers.registry.registry import register

logger = logging.getLogger("job_hunting.rozee")

BASE_URL = "https://www.rozee.pk"


@register(
    "rozee",
    display_name="Rozee.pk",
    locations=["Pakistan"],
    interval=30,
)
class RozeeScraper(BaseScraper):
    source = "rozee"

    async def fetch(self) -> list[str]:
        pages: list[str] = []
        page = await self.get_page()

        for city in ["Islamabad", "Rawalpindi", "Lahore"]:
            try:
                url = f"{BASE_URL}/jobs?location={city}"
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(5000)
                content = await page.content()
                pages.append(content)
                logger.debug("Fetched Rozee %s", city)
            except Exception:
                logger.exception("Failed Rozee %s", city)

        return pages

    async def parse(self, raw: Any) -> list[RawJob]:
        pages: list[str] = raw if isinstance(raw, list) else [str(raw)]
        jobs: list[RawJob] = []

        for page_html in pages:
            tree = parse_utils.from_html(page_html)
            links = tree.css("a[href*='/job/'], a[href*='job-detail'], .job-title a")

            for link in links:
                href = link.attributes.get("href", "") if hasattr(link, "attributes") else ""
                if not href:
                    continue

                full_url = urljoin(BASE_URL, str(href))
                title = link.text(strip=True) if hasattr(link, "text") else ""

                if not title or len(str(title)) < 3:
                    continue

                source_id = _extract_source_id(str(href), str(title))

                jobs.append(
                    RawJob(
                        title=str(title),
                        company="Rozee.pk",
                        location="Pakistan",
                        url=full_url,
                        apply_url=full_url,
                        source=self.source,
                        source_id=source_id,
                        posted_at=datetime.now(UTC),
                        is_remote=False,
                    )
                )

        return jobs


def _extract_source_id(href: str, fallback: str) -> str:
    parts = str(href).rstrip("/").rsplit("/", 1)
    if len(parts) == 2 and parts[1]:
        return f"rozee-{parts[1][:30]}"
    import hashlib

    return f"rozee-{hashlib.md5(fallback.encode()).hexdigest()[:10]}"
