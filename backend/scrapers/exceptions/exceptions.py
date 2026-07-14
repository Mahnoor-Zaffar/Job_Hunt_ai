"""Scraper-specific exception hierarchy.

All scraper exceptions inherit from ``ScraperError`` so callers can
catch a single base type when they do not care about the details.
"""


class ScraperError(Exception):
    """Base for all scraper-originated errors."""

    def __init__(self, message: str, source: str = "unknown") -> None:
        self.source = source
        self.message = message
        super().__init__(f"[{source}] {message}")


class FetchError(ScraperError):
    """Network-level failure (DNS, connection refused, HTTP error)."""


class ParseError(ScraperError):
    """Failure to extract data from a source response."""


class BrowserError(ScraperError):
    """Playwright / browser-level failure."""


class ScraperTimeoutError(ScraperError):
    """Request or operation exceeded its time limit."""


class RateLimitError(ScraperError):
    """Source responded with a rate-limit indicator."""


class NormalizationError(ScraperError):
    """Failure during data normalisation that cannot be recovered."""
