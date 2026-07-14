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

SELECTOR_JOB_CARD = "div.job-listing, div.listing-item, div.job-card"
SELECTOR_TITLE = "h2, h3, a.job-title, .title"
SELECTOR_COMPANY = ".company, .company-name"
SELECTOR_LOCATION = ".location, .city"
SELECTOR_URL = "a.apply, a[href*='/job'], a.job-title"
SELECTOR_DESCRIPTION = ".description, .desc"
SELECTOR_TYPE = ".type, .employment"
SELECTOR_EXPERIENCE = ".experience, .level"
SELECTOR_SALARY = ".salary, .salary-info"
SELECTOR_POSTED = ".posted, .date"


@register(
    "brightspyre",
    display_name="BrightSpyre.com",
    locations=["Pakistan"],
    interval=30,
)
class BrightSpyreScraper(BaseScraper):
    """Scraper for BrightSpyre.com — Pakistani job portal.

    Fetches search results filtered by supported cities and parses
    job listing cards using Selectolax.
    """

    source = "brightspyre"
    _MAX_PAGES = 5

    async def fetch(self) -> list[str]:
        pages: list[str] = []
        for location in SUPPORTED_LOCATIONS:
            for page in range(1, self._MAX_PAGES + 1):
                url = f"{SEARCH_URL}?sort=&page={page}&location={location}"
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
            cards = tree.css(SELECTOR_JOB_CARD)
            logger.debug("Parsing %d job cards", len(cards))

            for card in cards:
                card_html = card.html
                if card_html is None:
                    continue
                card_parser = parse_utils.from_html(card_html)
                raw_job = self._parse_card(card_parser)
                if raw_job:
                    jobs.append(raw_job)

        return jobs

    def _parse_card(self, tree: Any) -> RawJob | None:
        title = parse_utils.text(tree, SELECTOR_TITLE)
        if not title:
            return None

        company = parse_utils.text(tree, SELECTOR_COMPANY) or ""
        location = parse_utils.text(tree, SELECTOR_LOCATION) or ""
        url = parse_utils.attr(tree, SELECTOR_URL, "href") or ""
        full_url = urljoin(BASE_URL, url) if url else ""

        source_id = f"bs-{_id_from_url(full_url) if full_url else 'unknown'}"

        salary_text = parse_utils.text(tree, SELECTOR_SALARY)
        if salary_text:
            import re

            nums = re.findall(r"\d[\d,]*", salary_text.replace(",", ""))
            salary = float(nums[0]) if nums else None
        else:
            salary = None

        return RawJob(
            title=title,
            company=company,
            location=location,
            description=parse_utils.text(tree, SELECTOR_DESCRIPTION),
            url=full_url or f"{BASE_URL}/job",
            apply_url=full_url or None,
            source=self.source,
            source_id=source_id,
            salary_min=salary,
            salary_max=None,
            currency="PKR" if salary else None,
            employment_type=parse_utils.text(tree, SELECTOR_TYPE),
            experience_level=parse_utils.text(tree, SELECTOR_EXPERIENCE),
            posted_at=datetime.now(UTC),
            is_remote="remote" in (location or "").lower(),
            skills=None,
            requirements=None,
        )


def _id_from_url(url: str) -> str:
    parts = url.rstrip("/").rsplit("/", 1)
    if len(parts) == 2:
        return parts[1].rsplit("?")[0]
    import hashlib

    return hashlib.md5(url.encode()).hexdigest()[:10]
