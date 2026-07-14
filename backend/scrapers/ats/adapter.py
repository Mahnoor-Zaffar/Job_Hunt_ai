"""Base class for reusable ATS platform adapters.

Each ATS adapter implements ``fetch`` and ``parse`` for a specific
platform.  The :class:`ATSOrchestrator` dispatches company
configurations to the matching adapter without requiring per-company
scraper code.
"""

from abc import ABC, abstractmethod
from typing import Any

from backend.scrapers.ats.companies import CompanyConfig
from backend.scrapers.http.client import HttpClient
from backend.scrapers.models.models import RawJob


class BaseATSAdapter(ABC):
    """Abstract adapter for a single ATS platform.

    Subclasses must implement :meth:`fetch` and :meth:`parse`.
    The orchestrator handles error recovery, logging, and persistence.
    """

    platform: str = ""

    def __init__(self, http_client: HttpClient | None = None) -> None:
        self.http = http_client or HttpClient()

    @abstractmethod
    async def fetch(self, company: CompanyConfig) -> list[dict[str, Any]]:
        """Retrieve raw job data for *company* from the platform API."""

    @abstractmethod
    async def parse(
        self,
        raw: list[dict[str, Any]],
        company: CompanyConfig,
    ) -> list[RawJob]:
        """Convert raw API data into :class:`RawJob` objects."""

    async def close(self) -> None:
        await self.http.close()
