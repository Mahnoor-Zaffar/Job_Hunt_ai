from unittest.mock import AsyncMock, patch

import pytest

from backend.scrapers.models.models import RawJob
from backend.scrapers.remote import RemoteOKScraper

MOCK_API_RESPONSE = [
    {
        "id": 1,
        "position": "Senior Python Developer",
        "company": "Acme Inc",
        "location": "Remote",
        "url": "https://remoteok.com/1",
        "apply_url": "https://acme.com/apply",
        "tags": ["Python", "Docker", "AWS"],
        "salary_min": 80000,
        "salary_max": 120000,
        "salary_currency": "USD",
        "epoch": 1700000000,
        "description": "Great job requiring Python and Docker.",
    },
    {
        "id": 2,
        "position": "Frontend Engineer",
        "company": "WebCo",
        "location": "Worldwide",
        "url": "https://remoteok.com/2",
        "apply_url": "https://webco.com/apply",
        "tags": ["React", "TypeScript"],
        "salary_min": None,
        "salary_max": None,
        "salary_currency": "USD",
        "epoch": 1700001000,
        "description": "Build UIs with React.",
    },
]


class TestRemoteOKScraper:
    @pytest.mark.asyncio
    async def test_fetch_returns_jobs(self) -> None:
        scraper = RemoteOKScraper()
        with patch.object(
            scraper.http, "get_json", AsyncMock(return_value=MOCK_API_RESPONSE)
        ) as mock_get_json:
            result = await scraper.fetch()
            assert len(result) == 2
            mock_get_json.assert_called_once_with(
                "https://remoteok.com/api", headers={"Accept": "application/json"}
            )

    @pytest.mark.asyncio
    async def test_parse_extracts_fields(self) -> None:
        scraper = RemoteOKScraper()
        parsed = await scraper.parse(MOCK_API_RESPONSE)
        assert len(parsed) == 2

        job = parsed[0]
        assert isinstance(job, RawJob)
        assert job.title == "Senior Python Developer"
        assert job.company == "Acme Inc"
        assert job.location == "Remote"
        assert job.apply_url == "https://acme.com/apply"
        assert job.source == "remoteok"
        assert job.source_id == "remoteok-1"

    @pytest.mark.asyncio
    async def test_parse_tags_as_skills(self) -> None:
        scraper = RemoteOKScraper()
        parsed = await scraper.parse(MOCK_API_RESPONSE)
        assert parsed[0].skills == ["Python", "Docker", "AWS"]
        assert parsed[1].skills == ["React", "TypeScript"]

    @pytest.mark.asyncio
    async def test_parse_remote_type_is_remote(self) -> None:
        scraper = RemoteOKScraper()
        parsed = await scraper.parse(MOCK_API_RESPONSE)
        assert parsed[0].remote_type == "remote"
        assert parsed[0].is_remote is True
        assert parsed[1].remote_type == "remote"

    @pytest.mark.asyncio
    async def test_parse_salary_fields(self) -> None:
        scraper = RemoteOKScraper()
        parsed = await scraper.parse(MOCK_API_RESPONSE)
        assert parsed[0].salary_min == 80000.0
        assert parsed[0].salary_max == 120000.0
        assert parsed[0].currency == "USD"
        assert parsed[1].salary_min is None
        assert parsed[1].salary_max is None

    @pytest.mark.asyncio
    async def test_empty_response(self) -> None:
        scraper = RemoteOKScraper()
        parsed = await scraper.parse([])
        assert parsed == []

    @pytest.mark.asyncio
    async def test_fetch_filters_non_jobs(self) -> None:
        scraper = RemoteOKScraper()
        mixed = [*MOCK_API_RESPONSE, {"not_a_job": True}]
        with patch.object(scraper.http, "get_json", AsyncMock(return_value=mixed)):
            result = await scraper.fetch()
            assert len(result) == 2
