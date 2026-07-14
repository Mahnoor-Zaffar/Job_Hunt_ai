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
SEARCH_URL = f"{BASE_URL}/search"
SUPPORTED_QUERY = "islamabad OR rawalpindi OR lahore"

SELECTOR_JOB_CARD = "div.job-listing, div.job"
SELECTOR_TITLE = "h1, h2, h3, .job-title, .title"
SELECTOR_COMPANY = ".company-name, .company, .employer"
SELECTOR_LOCATION = ".location, .city"
SELECTOR_URL = "a.job-link, a[href*='/job']"
SELECTOR_DESCRIPTION = ".description, .detail"
SELECTOR_TYPE = ".type, .job-type"
SELECTOR_EXPERIENCE = ".experience, .level"
SELECTOR_SALARY = ".salary, .salary-range"
SELECTOR_POSTED = ".posted, .date, .created"


@register(
    "rozee",
    display_name="Rozee.pk",
    locations=["Pakistan"],
    interval=30,
)
class RozeeScraper(BaseScraper):
    """Scraper for Rozee.pk — Pakistan's largest job portal.

    Scrapes the search results page using ``httpx`` and Selectolax.
    Pagination is handled by appending ``?page=N`` to the search URL.
    """

    source = "rozee"
    _MAX_PAGES = 5

    async def fetch(self) -> list[str]:
        pages: list[str] = []
        for page in range(1, self._MAX_PAGES + 1):
            url = f"{SEARCH_URL}?page={page}&q={SUPPORTED_QUERY}"
            try:
                html = await self.http.get(url)
                pages.append(html)
                logger.debug("Fetched page %d from %s", page, url)
            except Exception:
                logger.exception("Failed to fetch page %d from %s", page, url)
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
            logger.debug("Found %d job cards on page", len(cards))

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

        source_id = self._extract_source_id(url or title)
        description = parse_utils.text(tree, SELECTOR_DESCRIPTION)
        employment_type = parse_utils.text(tree, SELECTOR_TYPE)
        experience_level = parse_utils.text(tree, SELECTOR_EXPERIENCE)
        salary_text = parse_utils.text(tree, SELECTOR_SALARY)
        posted_text = parse_utils.text(tree, SELECTOR_POSTED)

        salary_min, salary_max, currency = (
            _parse_salary_text(salary_text) if salary_text else (None, None, None)
        )
        posted_at = _parse_relative_date(posted_text) if posted_text else datetime.now(UTC)

        return RawJob(
            title=title,
            company=company,
            location=location,
            description=description,
            url=full_url or f"{BASE_URL}/job",
            apply_url=full_url or None,
            source=self.source,
            source_id=source_id,
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            employment_type=employment_type,
            experience_level=experience_level,
            posted_at=posted_at,
            is_remote=" remote" in (location or "").lower(),
        )

    def _extract_source_id(self, value: str) -> str:
        parts = value.rsplit("-", 1)
        if len(parts) == 2 and parts[1].isdigit():
            return f"rozee-{parts[1]}"
        import hashlib

        return f"rozee-{hashlib.md5(value.encode()).hexdigest()[:10]}"


def _parse_salary_text(salary_text: str) -> tuple[float | None, float | None, str | None]:
    import re

    salary_text = salary_text.replace(",", "").strip()
    numbers = re.findall(r"[\d.,]+", salary_text)
    if not numbers:
        return None, None, None

    currency = None
    for symbol, code in [("$", "USD"), ("€", "EUR"), ("£", "GBP"), ("Rs", "PKR")]:
        if symbol in salary_text:
            currency = code
            break

    values = []
    for n in numbers[:2]:
        try:
            values.append(float(n))
        except ValueError:
            continue

    if len(values) == 1:
        return values[0], None, currency
    elif len(values) >= 2:
        return values[0], values[1], currency
    return None, None, None


def _parse_relative_date(text: str) -> datetime | None:
    import re

    text = text.strip().lower()
    now = datetime.now(UTC)

    match = re.search(r"(\d+)\s*(day|week|month|hour|min|minute)", text)
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        if "min" in unit:
            return now
        elif "hour" in unit:
            from datetime import timedelta

            return now - timedelta(hours=value)
        elif "day" in unit:
            from datetime import timedelta

            return now - timedelta(days=value)
        elif "week" in unit:
            from datetime import timedelta

            return now - timedelta(weeks=value)
        elif "month" in unit:
            from datetime import timedelta

            return now - timedelta(days=value * 30)

    if "today" in text or "hours" in text:
        return now
    if "yesterday" in text:
        from datetime import timedelta

        return now - timedelta(days=1)

    return now
