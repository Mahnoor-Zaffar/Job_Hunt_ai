"""Unit tests for the scraper framework.

Tests are organised by component and use plain pytest fixtures so
they can run without a database or external services.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.config.config import ScraperSettings
from backend.scrapers.exceptions import (
    BrowserError,
    FetchError,
    NormalizationError,
    ParseError,
    RateLimitError,
    ScraperError,
    ScraperTimeoutError,
)
from backend.scrapers.http.client import HttpClient
from backend.scrapers.models.models import NormalizedJob, RawJob
from backend.scrapers.normalizer.normalizer import Normalizer
from backend.scrapers.parser import parser as parse_utils
from backend.scrapers.registry.registry import ScraperRegistry, register
from backend.scrapers.validator.validator import Validator

# ------------------------------------------------------------------
# Exception hierarchy
# ------------------------------------------------------------------


class TestExceptions:
    def test_scraper_error_base(self) -> None:
        err = ScraperError("test", source="example")
        assert err.source == "example"
        assert "test" in str(err)

    @pytest.mark.parametrize(
        "exc_cls",
        [
            FetchError,
            ParseError,
            BrowserError,
            ScraperTimeoutError,
            RateLimitError,
            NormalizationError,
        ],
    )
    def test_all_exception_types(self, exc_cls: type) -> None:
        err = exc_cls("msg", source="test")
        assert err.source == "test"
        assert isinstance(err, ScraperError)


# ------------------------------------------------------------------
# Normalizer
# ------------------------------------------------------------------


class TestNormalizer:
    @pytest.fixture
    def normalizer(self) -> Normalizer:
        return Normalizer()

    def test_normalize_minimal_job(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="  Python  Developer  ",
            company="  Acme  ",
            location="Islamabad, Pakistan",
            url="https://example.com/job/1",
            source="example",
            source_id="1",
            is_remote=False,
        )
        nj = normalizer.normalize(raw)
        assert nj.title == "Python Developer"
        assert nj.company == "Acme"
        assert nj.location == "Islamabad, Pakistan"
        assert nj.city == "Islamabad"
        assert nj.country == "Pakistan"
        assert nj.fingerprint

    def test_normalize_remote_job(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="Remote Engineer",
            company="Remote Corp",
            location="Remote",
            url="https://example.com/job/2",
            source="example",
            source_id="2",
            is_remote=True,
        )
        nj = normalizer.normalize(raw)
        assert nj.is_remote is True
        assert nj.location == "Remote"

    def test_normalize_salary(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="Dev",
            company="Co",
            location="Lahore",
            url="https://x.com/job/3",
            source="x",
            source_id="3",
            salary_min=50000.0,
            salary_max=80000.0,
            currency="USD",
        )
        nj = normalizer.normalize(raw)
        assert nj.salary_min == 50000.0
        assert nj.salary_max == 80000.0
        assert nj.currency == "USD"

    def test_normalize_employment_type(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="Dev",
            company="Co",
            location="Lahore",
            url="https://x.com/job/4",
            source="x",
            source_id="4",
            employment_type="Full Time",
        )
        nj = normalizer.normalize(raw)
        assert nj.employment_type == "full_time"

    def test_normalize_unknown_city(self, normalizer: Normalizer) -> None:
        raw = RawJob(
            title="Dev",
            company="Co",
            location="New York, USA",
            url="https://x.com/job/5",
            source="x",
            source_id="5",
        )
        nj = normalizer.normalize(raw)
        assert nj.country == "United States"
        assert nj.city is None


# ------------------------------------------------------------------
# Validator
# ------------------------------------------------------------------


class TestValidator:
    @pytest.fixture
    def validator(self) -> Validator:
        return Validator()

    def test_valid_job(self, validator: Validator) -> None:
        job = NormalizedJob(
            title="Engineer",
            company="Acme",
            location="Remote",
            url="https://example.com",
            source="example",
            source_id="1",
            is_remote=True,
            fingerprint="abc123",
        )
        result = validator.validate(job)
        assert result.is_valid
        assert not result.errors

    def test_missing_required_field(self, validator: Validator) -> None:
        job = NormalizedJob(
            title="",
            company="Acme",
            location="Remote",
            url="https://example.com",
            source="example",
            source_id="1",
            is_remote=True,
            fingerprint="abc123",
        )
        result = validator.validate(job)
        assert not result.is_valid
        assert any("title" in e for e in result.errors)

    def test_invalid_url(self, validator: Validator) -> None:
        job = NormalizedJob(
            title="Engineer",
            company="Acme",
            location="Remote",
            url="not-a-url",
            source="example",
            source_id="1",
            is_remote=True,
            fingerprint="abc123",
        )
        result = validator.validate(job)
        assert not result.is_valid

    def test_salary_warning(self, validator: Validator) -> None:
        job = NormalizedJob(
            title="Engineer",
            company="Acme",
            location="Remote",
            url="https://example.com",
            source="example",
            source_id="1",
            is_remote=True,
            fingerprint="abc123",
            salary_min=20000,
            salary_max=10000,
        )
        result = validator.validate(job)
        assert result.is_valid
        assert any("min" in w.lower() for w in result.warnings)


# ------------------------------------------------------------------
# Parser utilities
# ------------------------------------------------------------------


class TestParser:
    HTML_FRAGMENT = """
    <html><body>
        <h1 class="title">Senior Engineer</h1>
        <div class="company">Test Corp</div>
        <a class="link" href="https://apply.com/1">Apply</a>
        <ul class="items">
            <li>A</li>
            <li>B</li>
            <li>C</li>
        </ul>
    </body></html>
    """

    def test_text_extraction(self) -> None:
        tree = parse_utils.from_html(self.HTML_FRAGMENT)
        title = parse_utils.text(tree, "h1.title")
        assert title == "Senior Engineer"

    def test_text_missing_selector(self) -> None:
        tree = parse_utils.from_html(self.HTML_FRAGMENT)
        result = parse_utils.text(tree, ".nonexistent")
        assert result is None

    def test_attr_extraction(self) -> None:
        tree = parse_utils.from_html(self.HTML_FRAGMENT)
        href = parse_utils.attr(tree, "a.link", "href")
        assert href == "https://apply.com/1"

    def test_all_texts(self) -> None:
        tree = parse_utils.from_html(self.HTML_FRAGMENT)
        items = parse_utils.texts(tree, ".items li")
        assert items == ["A", "B", "C"]


# ------------------------------------------------------------------
# HTTP Client
# ------------------------------------------------------------------


class TestHttpClient:
    @pytest.mark.asyncio
    async def test_get_success(self) -> None:
        client = HttpClient()
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.text = "hello"
        mock_resp.raise_for_status = MagicMock()

        with patch.object(client, "_get_client") as get_cli:
            mock_cli = AsyncMock()
            mock_cli.get = AsyncMock(return_value=mock_resp)
            get_cli.return_value = mock_cli
            result = await client.get("https://example.com")
            assert result == "hello"

        await client.close()

    @pytest.mark.asyncio
    async def test_get_retry_on_timeout(self) -> None:
        import httpx

        client = HttpClient(max_retries=3)
        mock_cli = AsyncMock()
        mock_cli.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

        with patch.object(client, "_get_client", return_value=mock_cli), pytest.raises(FetchError):
            await client.get("https://example.com")

        await client.close()


# ------------------------------------------------------------------
# BaseScraper (with a concrete mock)
# ------------------------------------------------------------------


class MockConcreteScraper(BaseScraper):
    source = "mock_test"

    async def fetch(self) -> str:
        return '<div class="job"><h2>Test Job</h2></div>'

    async def parse(self, raw: str) -> list[RawJob]:
        return [
            RawJob(
                title="Test Job",
                company="Mock Corp",
                location="Remote",
                url="https://example.com/job",
                source=self.source,
                source_id="test-001",
                is_remote=True,
            )
        ]


class TestBaseScraper:
    @pytest.mark.asyncio
    async def test_scrape_returns_normalized_jobs(self) -> None:
        scraper = MockConcreteScraper()
        result = await scraper.scrape()
        assert len(result) == 1
        assert isinstance(result[0], NormalizedJob)
        assert result[0].title == "Test Job"
        assert result[0].is_remote
        assert result[0].fingerprint

    @pytest.mark.asyncio
    async def test_empty_parse(self) -> None:
        class EmptyScraper(BaseScraper):
            source = "empty"

            async def fetch(self) -> str:
                return ""

            async def parse(self, raw: str) -> list[RawJob]:
                return []

        scraper = EmptyScraper()
        result = await scraper.scrape()
        assert result == []

    @pytest.mark.asyncio
    async def test_cleanup_is_noop_by_default(self) -> None:
        scraper = MockConcreteScraper()
        result = scraper.cleanup()
        assert result is None


# ------------------------------------------------------------------
# Registry
# ------------------------------------------------------------------


class TestRegistry:
    def test_register_and_get(self) -> None:
        registry = ScraperRegistry()

        @register("test_registry", display_name="Test", locations=["Remote"])
        class RegTestScraper(BaseScraper):
            source = "test_registry"

            async def fetch(self) -> str:
                return ""

            async def parse(self, raw: str) -> list[RawJob]:
                return []

        cls = registry.get("test_registry")
        assert cls is not None
        assert cls.source == "test_registry"

    def test_get_metadata(self) -> None:
        registry = ScraperRegistry()
        meta = registry.get_metadata("example")
        if meta is not None:
            assert "source" in meta

    def test_list_sources(self) -> None:
        registry = ScraperRegistry()
        sources = registry.list_sources()
        assert isinstance(sources, list)

    def test_get_enabled_empty_settings(self) -> None:
        registry = ScraperRegistry()
        settings = ScraperSettings(ENABLED_SCRAPERS=[], DISABLED_SCRAPERS=[])
        enabled = registry.get_enabled(settings)
        assert isinstance(enabled, list)


# ------------------------------------------------------------------
# Example scraper integration
# ------------------------------------------------------------------


class TestExampleScraper:
    @pytest.mark.asyncio
    async def test_example_scrape(self) -> None:
        from backend.scrapers.example.scraper import MockHTMLScraper

        scraper = MockHTMLScraper()
        result = await scraper.scrape()
        assert len(result) == 1
        assert result[0].title == "Senior Python Engineer"
        assert result[0].company == "Acme Corp"
        assert result[0].city == "Islamabad"
        assert result[0].country == "Pakistan"
        assert result[0].employment_type == "full_time"
        assert result[0].experience_level == "senior"
        assert result[0].fingerprint
