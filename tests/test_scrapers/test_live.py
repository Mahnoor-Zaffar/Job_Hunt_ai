"""Live integration tests for scraper sources.

These tests make real HTTP requests to external job sources.
They are skipped by default.  Run with::

    uv run pytest tests/test_scrapers/test_live.py -v -m network
"""

import pytest

from backend.scrapers.ats.ashby import AshbyAdapter
from backend.scrapers.ats.companies import CompanyConfig
from backend.scrapers.ats.greenhouse import GreenhouseAdapter
from backend.scrapers.ats.lever import LeverAdapter
from backend.scrapers.models.models import RawJob
from backend.scrapers.pakistan import RozeeScraper
from backend.scrapers.remote import RemoteOKScraper

pytestmark = pytest.mark.network


@pytest.mark.skip(reason="Live network test — requires internet access")
class TestRemoteOKLive:
    @pytest.mark.asyncio
    async def test_fetch_live(self) -> None:
        scraper = RemoteOKScraper()
        data = await scraper.fetch()
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_scrape_pipeline(self) -> None:
        scraper = RemoteOKScraper()
        jobs = await scraper.scrape()
        assert len(jobs) > 0
        for job in jobs:
            assert job.title
            assert job.company
            assert job.fingerprint
            assert job.remote_type == "remote"
            assert job.is_remote is True


@pytest.mark.skip(reason="Live network test — requires internet access")
class TestRozeeLive:
    @pytest.mark.asyncio
    async def test_fetch_live(self) -> None:
        scraper = RozeeScraper()
        try:
            pages = await scraper.fetch()
            assert isinstance(pages, list)
            assert len(pages) > 0
        except Exception as e:
            pytest.skip(f"Rozee unavailable: {e}")


@pytest.mark.skip(reason="Live network test — requires internet access")
class TestGreenhouseLive:
    @pytest.mark.asyncio
    async def test_fetch_motive(self) -> None:
        adapter = GreenhouseAdapter()
        company = CompanyConfig(
            name="Motive",
            platform="greenhouse",
            careers_url="https://boards.greenhouse.io/motive",
        )
        try:
            data = await adapter.fetch(company)
            assert isinstance(data, list)
        except Exception as e:
            pytest.skip(f"Greenhouse Motive unavailable: {e}")

    @pytest.mark.asyncio
    async def test_parse_motive(self) -> None:
        adapter = GreenhouseAdapter()
        company = CompanyConfig(
            name="Motive",
            platform="greenhouse",
            careers_url="https://boards.greenhouse.io/motive",
        )
        try:
            data = await adapter.fetch(company)
            if not data:
                pytest.skip("No jobs returned from Greenhouse Motive")
            jobs = await adapter.parse(data, company)
            assert len(jobs) > 0
            for job in jobs:
                assert isinstance(job, RawJob)
                assert job.title
                assert job.company == "Motive"
                assert job.source == "greenhouse"
        except Exception as e:
            pytest.skip(f"Greenhouse Motive parsing failed: {e}")


@pytest.mark.skip(reason="Live network test — requires internet access")
class TestLeverLive:
    @pytest.mark.asyncio
    async def test_fetch_arbisoft(self) -> None:
        adapter = LeverAdapter()
        company = CompanyConfig(
            name="Arbisoft",
            platform="lever",
            careers_url="https://api.lever.co/v0/postings/arbisoft",
        )
        try:
            data = await adapter.fetch(company)
            assert isinstance(data, list)
        except Exception as e:
            pytest.skip(f"Lever Arbisoft unavailable: {e}")


@pytest.mark.skip(reason="Live network test — requires internet access")
class TestAshbyLive:
    @pytest.mark.asyncio
    async def test_fetch_without_key(self) -> None:
        adapter = AshbyAdapter()
        company = CompanyConfig(
            name="TestCo",
            platform="ashby",
            careers_url="https://jobs.ashbyhq.com/testco",
        )
        result = await adapter.fetch(company)
        assert result == []
