"""Indeed scraper — requires Playwright for JS rendering."""

import logging
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin

from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.models.models import RawJob
from backend.scrapers.parser import parser as parse_utils
from backend.scrapers.registry.registry import register

logger = logging.getLogger("job_hunting.indeed")

BASE_URL = "https://pk.indeed.com"
SUPPORTED_LOCATIONS = ["Islamabad", "Rawalpindi", "Lahore"]


@register(
    "indeed",
    display_name="Indeed",
    locations=["Pakistan"],
    interval=30,
)
class IndeedScraper(BaseScraper):
    source = "indeed"

    async def fetch(self) -> list[str]:
        pages: list[str] = []
        for location in SUPPORTED_LOCATIONS:
            try:
                page = await self.get_page()
                url = f"{BASE_URL}/jobs?q=software+engineer&l={location}&sort=date"
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(4000)
                content = await page.content()
                pages.append(content)
                logger.debug("Fetched Indeed %s", location)
            except Exception:
                logger.exception("Failed Indeed %s", location)
        return pages

    async def parse(self, raw: Any) -> list[RawJob]:
        pages: list[str] = raw if isinstance(raw, list) else [str(raw)]
        jobs: list[RawJob] = []

        for page_html in pages:
            tree = parse_utils.from_html(page_html)

            for card in tree.css(
                "div.job_seen_beacon, td.resultContent, div[class*='cardOutline'], div.slider_item"
            ):
                try:
                    card_html = card.html
                    if card_html is None:
                        continue
                    card_parser = parse_utils.from_html(card_html)
                    raw_job = self._parse_card(card_parser)
                    if raw_job:
                        jobs.append(raw_job)
                except Exception:
                    continue

            for link in tree.css("a[id^='job_'], h2.jobTitle a, a[data-jk]"):
                try:
                    title = link.text(strip=True) if hasattr(link, "text") else ""
                    if not title or len(str(title)) < 3:
                        continue
                    href = link.attributes.get("href", "") if hasattr(link, "attributes") else ""
                    if not href:
                        continue

                    full_url = urljoin(BASE_URL, str(href))
                    job_id = _extract_job_key(str(href))

                    parent_text = ""
                    if hasattr(link, "parent") and link.parent is not None:
                        parent_text = link.parent.text() or ""

                    jobs.append(
                        RawJob(
                            title=str(title),
                            company="Indeed",
                            location="Pakistan",
                            description=parent_text[:1000] if parent_text else None,
                            url=full_url,
                            apply_url=full_url,
                            source=self.source,
                            source_id=f"indeed-{job_id}",
                            posted_at=datetime.now(UTC),
                        )
                    )
                except Exception:
                    continue

        return jobs

    def _parse_card(self, tree: Any) -> RawJob | None:
        title_el = tree.css_first("h2 a, a[id^='job_'], .jobTitle a")
        if title_el is None:
            return None

        title = (title_el.text(strip=True) or "").strip()
        if not title or len(title) < 3:
            return None

        href = title_el.attributes.get("href", "") if hasattr(title_el, "attributes") else ""
        full_url = urljoin(BASE_URL, str(href)) if href else ""

        company_el = tree.css_first(".companyName, .company_name, [data-testid='company-name']")
        company = (company_el.text(strip=True) or "") if company_el else "Indeed"

        loc_el = tree.css_first(".companyLocation, .location, [data-testid='text-location']")
        location = (loc_el.text(strip=True) or "") if loc_el else "Pakistan"

        job_id = _extract_job_key(str(href))

        return RawJob(
            title=title,
            company=company,
            location=location,
            description=None,
            url=full_url,
            apply_url=full_url,
            source=self.source,
            source_id=f"indeed-{job_id}",
            posted_at=datetime.now(UTC),
            is_remote="remote" in location.lower(),
        )


def _extract_job_key(href: str) -> str:
    import re

    match = re.search(r"[?&]jk=([a-f0-9]+)", href)
    if match:
        return match.group(1)
    parts = href.rstrip("/").rsplit("/", 1)
    if len(parts) == 2 and parts[1]:
        return parts[1][:20]
    import hashlib

    return hashlib.md5(href.encode()).hexdigest()[:10]
