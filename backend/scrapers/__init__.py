"""Scraper framework for the Job Hunting platform.

Every directory under this package serves a single responsibility.
See ``scrapers/base/scraper.py`` for the abstract interface that all
job-source scrapers must implement.

Quick-start::

    from backend.scrapers.orchestrator import ScraperOrchestrator
    from backend.scrapers.registry import ScraperRegistry

    orchestrator = ScraperOrchestrator()
    summary = await orchestrator.run_all()
"""

from backend.scrapers.ats import (
    AshbyAdapter,
    ATSOrchestrator,
    BaseATSAdapter,
    CompanyConfig,
    GreenhouseAdapter,
    LeverAdapter,
    WorkableAdapter,
    load_companies,
)
from backend.scrapers.base import BaseScraper
from backend.scrapers.browser.manager import BrowserManager
from backend.scrapers.config.config import ScraperSettings
from backend.scrapers.exceptions import ScraperError
from backend.scrapers.http.client import HttpClient
from backend.scrapers.models.models import (
    ExecutionSummary,
    NormalizedJob,
    RawJob,
    RemoteType,
    ScraperResult,
    ValidationResult,
)
from backend.scrapers.normalizer.normalizer import Normalizer
from backend.scrapers.orchestrator.orchestrator import ScraperOrchestrator
from backend.scrapers.pakistan import BrightSpyreScraper, MustakbilScraper, RozeeScraper
from backend.scrapers.registry.registry import ScraperRegistry, register
from backend.scrapers.remote import RemoteOKScraper, RemotiveScraper, WeWorkRemotelyScraper
from backend.scrapers.technologies import TechnologyExtractor, extract_technologies
from backend.scrapers.validator.validator import Validator

__all__ = [
    "ATSOrchestrator",
    "AshbyAdapter",
    "BaseATSAdapter",
    "BaseScraper",
    "BrightSpyreScraper",
    "BrowserManager",
    "CompanyConfig",
    "ExecutionSummary",
    "GreenhouseAdapter",
    "HttpClient",
    "LeverAdapter",
    "MustakbilScraper",
    "NormalizedJob",
    "Normalizer",
    "RawJob",
    "RemoteOKScraper",
    "RemoteType",
    "RemotiveScraper",
    "RozeeScraper",
    "ScraperError",
    "ScraperOrchestrator",
    "ScraperRegistry",
    "ScraperResult",
    "ScraperSettings",
    "TechnologyExtractor",
    "ValidationResult",
    "Validator",
    "WeWorkRemotelyScraper",
    "WorkableAdapter",
    "extract_technologies",
    "load_companies",
    "register",
]
