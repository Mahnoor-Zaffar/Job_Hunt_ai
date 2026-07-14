import logging
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin

from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.models.models import RawJob
from backend.scrapers.parser import parser as parse_utils
from backend.scrapers.registry.registry import register

logger = logging.getLogger("job_hunting.weworkremotely")

BASE_URL = "https://weworkremotely.com"
SEARCH_URL = f"{BASE_URL}/categories/remote-programming-jobs"

SELECTOR_JOB_CARD = "li.feature, li.new-listing, section.jobs article"
SELECTOR_TITLE = "a, h3, h4, .title"
SELECTOR_COMPANY = ".company, .company-name"
SELECTOR_LOCATION = ".region, .location"
SELECTOR_URL = "a[href*='/remote-jobs/'], a"
SELECTOR_DESCRIPTION = ".description, .listing-details"
SELECTOR_TYPE = ".type, .job-type"
SELECTOR_POSTED = ".date, .posted"


@register(
    "weworkremotely",
    display_name="We Work Remotely",
    locations=["Remote"],
    interval=30,
)
class WeWorkRemotelyScraper(BaseScraper):
    """Scraper for WeWorkRemotely.com — the largest remote work community.

    Scrapes the remote programming category and parses each job listing
    card using Selectolax.
    """

    source = "weworkremotely"
    _MAX_PAGES = 3

    async def fetch(self) -> list[str]:
        pages: list[str] = []
        urls = [SEARCH_URL] + [f"{SEARCH_URL}?page={p}" for p in range(2, self._MAX_PAGES + 1)]
        for url in urls:
            try:
                html = await self.http.get(url)
                pages.append(html)
                logger.debug("Fetched %s", url)
            except Exception:
                logger.exception("Failed to fetch %s", url)
                if url == urls[0]:
                    raise
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
        url = parse_utils.attr(tree, SELECTOR_URL, "href") or ""
        full_url = urljoin(BASE_URL, url) if url else ""

        source_id = _derive_source_id(full_url, f"{company}-{title}")

        posted_text = parse_utils.text(tree, SELECTOR_POSTED)
        posted_at = None
        if posted_text:
            posted_at = _parse_posted_date(posted_text)

        return RawJob(
            title=title,
            company=company,
            location=parse_utils.text(tree, SELECTOR_LOCATION) or "Remote",
            description=parse_utils.text(tree, SELECTOR_DESCRIPTION),
            url=full_url or f"{BASE_URL}/remote-jobs/",
            apply_url=full_url or None,
            source=self.source,
            source_id=source_id,
            employment_type=parse_utils.text(tree, SELECTOR_TYPE),
            posted_at=posted_at or datetime.now(UTC),
            is_remote=True,
            remote_type="remote",
            salary_min=None,
            salary_max=None,
            currency=None,
            skills=None,
            requirements=None,
            experience_level=None,
        )


def _derive_source_id(url: str, fallback: str) -> str:
    cleaned = url.rstrip("/").rsplit("/", 1)
    if len(cleaned) == 2:
        return f"wwr-{cleaned[1].rsplit('?')[0]}"
    import hashlib

    return f"wwr-{hashlib.md5(fallback.encode()).hexdigest()[:10]}"


def _parse_posted_date(text: str) -> datetime | None:
    import re

    lower = text.strip().lower()
    now = datetime.now(UTC)
    from datetime import timedelta

    match = re.search(r"(\d+)\s*(d|day|h|hour|w|week|m|month)", lower)
    if not match:
        return now

    value = int(match.group(1))
    unit = match.group(2)
    if unit in ("d", "day"):
        return now - timedelta(days=value)
    if unit in ("h", "hour"):
        return now - timedelta(hours=value)
    if unit in ("w", "week"):
        return now - timedelta(weeks=value)
    if unit in ("m", "month"):
        return now - timedelta(days=value * 30)
    return now
