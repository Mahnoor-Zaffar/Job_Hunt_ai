import logging
import time
from abc import ABC, abstractmethod
from typing import Any, ClassVar

from playwright.async_api import Page

from backend.scrapers.browser.manager import BrowserManager
from backend.scrapers.config.config import ScraperSettings
from backend.scrapers.exceptions import BrowserError, ScraperError
from backend.scrapers.http.client import HttpClient
from backend.scrapers.models.models import (
    NormalizedJob,
    RawJob,
    ValidationResult,
)
from backend.scrapers.normalizer.normalizer import Normalizer
from backend.scrapers.validator.validator import Validator

logger = logging.getLogger("job_hunting.scraper")


class BaseScraper(ABC):
    """Abstract base class that all job-source scrapers must implement."""

    source: str
    display_name: str = ""
    supported_locations: ClassVar[list[str]] = []
    scrape_interval_minutes: int = 30
    concurrency_limit: int = 1

    def __init__(
        self,
        http_client: HttpClient | None = None,
        normalizer: Normalizer | None = None,
        validator: Validator | None = None,
        settings: ScraperSettings | None = None,
        browser_manager: BrowserManager | None = None,
    ) -> None:
        self.http = http_client or HttpClient()
        self._normalizer = normalizer or Normalizer()
        self._validator = validator or Validator()
        self._settings = settings or ScraperSettings()
        self._browser_manager = browser_manager

        if not self.display_name:
            self.display_name = self.source.replace("_", " ").title()

    # -- public API ---------------------------------------------------

    async def scrape(self) -> list[NormalizedJob]:
        start = time.perf_counter()

        raw_data = await self.fetch()
        raw_jobs = await self.parse(raw_data)

        normalized: list[NormalizedJob] = []
        for rj in raw_jobs:
            try:
                nj = self.normalize(rj)
                vr = self.validate(nj)
                if vr.is_valid:
                    normalized.append(nj)
                else:
                    logger.warning(
                        "[%s] job %s failed validation: %s",
                        self.source,
                        rj.source_id,
                        "; ".join(vr.errors),
                    )
            except ScraperError:
                logger.exception("[%s] error normalising job %s", self.source, rj.source_id)

        duration = time.perf_counter() - start
        logger.info(
            "[%s] scraped %d jobs in %.2fs",
            self.source,
            len(normalized),
            duration,
        )
        return normalized

    # -- abstract methods (implement in subclasses) -------------------

    @abstractmethod
    async def fetch(self) -> Any:
        """Retrieve raw data from the source.

        May use ``self.http`` for HTTP requests or the injected
        ``browser_manager`` (passed separately at orchestration time)
        for JavaScript-rendered pages.
        """

    @abstractmethod
    async def parse(self, raw: Any) -> list[RawJob]:
        """Convert raw source data into a list of ``RawJob`` objects."""

    # -- overridable methods ------------------------------------------

    def normalize(self, raw: RawJob) -> NormalizedJob:
        return self._normalizer.normalize(raw)

    def validate(self, job: NormalizedJob) -> ValidationResult:
        return self._validator.validate(job)

    async def get_page(self) -> Page:
        """Return a Playwright page for JavaScript-rendered content.

        Requires a ``BrowserManager`` to have been injected at
        construction time.  Raises ``BrowserError`` when the browser
        is unavailable.
        """
        if self._browser_manager is None:
            raise BrowserError(
                "BrowserManager not available — inject one at construction time",
                source=self.source,
            )
        return await self._browser_manager.get_page()

    def cleanup(self) -> None:  # noqa: B027
        """Release any resources held by this scraper instance.

        Override when your scraper acquires long-lived resources
        (e.g. open files, persistent connections).
        """
