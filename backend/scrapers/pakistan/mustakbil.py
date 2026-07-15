"""Mustakbil scraper — Angular SPA requiring Playwright for JS rendering."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urljoin

from selectolax.parser import HTMLParser

from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.models.models import RawJob
from backend.scrapers.registry.registry import register

logger = logging.getLogger("job_hunting.mustakbil")

BASE_URL = "https://www.mustakbil.com"
SUPPORTED_LOCATIONS = ["Islamabad", "Rawalpindi", "Lahore"]


@register(
    "mustakbil",
    display_name="Mustakbil.com",
    locations=["Pakistan"],
    interval=30,
)
class MustakbilScraper(BaseScraper):
    source = "mustakbil"

    async def fetch(self) -> list[str]:
        pages: list[str] = []
        for location in SUPPORTED_LOCATIONS:
            url = f"{BASE_URL}/jobs?search=software&location={location}"
            try:
                page = await self.get_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_selector("a.job-card__title", timeout=15000)
                await page.wait_for_timeout(2000)
                content = await page.content()
                pages.append(content)
                logger.debug("Fetched %s from Mustakbil", location)
            except Exception:
                logger.exception("Failed to fetch Mustakbil %s", location)
        return pages

    async def parse(self, raw: Any) -> list[RawJob]:
        pages: list[str] = raw if isinstance(raw, list) else [str(raw)]
        jobs: list[RawJob] = []

        for page_html in pages:
            tree = HTMLParser(page_html)

            for card in tree.css("div.job-card"):
                try:
                    raw_job = self._parse_card(card)
                    if raw_job:
                        jobs.append(raw_job)
                except Exception:
                    continue

            if not jobs:
                for link in tree.css("a.job-card__title"):
                    try:
                        raw_job = self._parse_from_title_link(link, tree)
                        if raw_job:
                            jobs.append(raw_job)
                    except Exception:
                        continue

        return jobs

    def _parse_card(self, card: Any) -> RawJob | None:
        title_el = card.css_first("a.job-card__title")
        if title_el is None:
            return None

        title = (title_el.text(strip=True) or "").strip()
        if not title:
            return None

        href = title_el.attributes.get("href", "")
        full_url = urljoin(BASE_URL, href) if href else ""

        company_el = card.css_first(".job-card__company")
        company = (company_el.text(strip=True) or "") if company_el else ""
        if not company:
            title_attr = title_el.attributes.get("title", "")
            if " at " in title_attr:
                company = title_attr.split(" at ", 1)[1].strip()

        loc_el = card.css_first(".job-card__location")
        location = (loc_el.text(strip=True) or "") if loc_el else ""

        time_el = card.css_first(".job-card__time")
        posted_text = (time_el.text(strip=True) or "") if time_el else ""

        source_id = _make_source_id(full_url, title)

        return RawJob(
            title=title,
            company=company or "Unknown",
            location=location,
            url=full_url or f"{BASE_URL}/job",
            apply_url=full_url or None,
            source=self.source,
            source_id=source_id,
            posted_at=_parse_date(posted_text),
            is_remote="remote" in location.lower(),
        )

    def _parse_from_title_link(self, link: Any, tree: Any) -> RawJob | None:
        title = (link.text(strip=True) or "").strip()
        if not title:
            return None

        href = link.attributes.get("href", "")
        full_url = urljoin(BASE_URL, href) if href else ""

        title_attr = link.attributes.get("title", "")
        company = ""
        if " at " in title_attr:
            company = title_attr.split(" at ", 1)[1].strip()

        loc_el = tree.css_first(".job-card__location")
        location = (loc_el.text(strip=True) or "") if loc_el else ""

        return RawJob(
            title=title,
            company=company or "Unknown",
            location=location,
            url=full_url or f"{BASE_URL}/job",
            apply_url=full_url or None,
            source=self.source,
            source_id=_make_source_id(full_url, title),
            is_remote="remote" in location.lower(),
        )


def _make_source_id(url: str, fallback: str) -> str:
    parts = url.rstrip("/").rsplit("/", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return f"mb-{parts[1]}"
    import hashlib

    return f"mb-{hashlib.md5(fallback.encode()).hexdigest()[:10]}"


def _parse_date(text: str) -> datetime | None:
    import re

    text = text.strip().lower()
    now = datetime.now(UTC)
    match = re.search(r"(\d+)\s*(day|week|month|hour|min|minute)", text)
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        if "min" in unit or "hour" in unit:
            return now
        if "day" in unit:
            return now - timedelta(days=value)
        if "week" in unit:
            return now - timedelta(weeks=value)
        if "month" in unit:
            return now - timedelta(days=value * 30)
    return now
