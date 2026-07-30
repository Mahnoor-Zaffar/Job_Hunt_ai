from unittest.mock import AsyncMock, patch

import pytest

from backend.scrapers.ats.ashby import AshbyAdapter
from backend.scrapers.ats.companies import CompanyConfig
from backend.scrapers.ats.greenhouse import (
    GreenhouseAdapter,
    _extract_next_jobs,
    _extract_remix_jobs,
)
from backend.scrapers.ats.lever import LeverAdapter
from backend.scrapers.models.models import RawJob


GH_MOCK_JOB = {
    "id": 12345,
    "title": "Backend Engineer",
    "absolute_url": "https://boards.greenhouse.io/testco/jobs/12345",
    "location": {"name": "Remote"},
    "metadata": [
        {"name": "Employment Type", "value": ["Full-time"]},
        {"name": "Experience Level", "value": ["Senior"]},
    ],
    "content": "# Backend Engineer\n\nWe are hiring!",
    "updated_at": "2024-01-15T10:00:00Z",
}

def _remix_html(jobs):
    import json
    data = {
        "state": {
            "loaderData": {
                "__remix_route": {
                    "jobPosts": {"data": jobs}
                }
            }
        }
    }
    return f'<script>window.__remixContext = {json.dumps(data)};</script>'


LEVER_MOCK_JOB = {
    "id": "abc-def",
    "text": "Software Engineer",
    "hostedUrl": "https://jobs.lever.co/testco/abc-def",
    "categories": {
        "location": "Remote",
        "commitment": "Full-time",
        "team": "Engineering",
    },
    "descriptionPlain": "We are hiring a Software Engineer",
    "createdAt": 1700000000000,
    "salaryRange": {"min": 60000, "max": 90000, "currency": "USD"},
}

ASHBY_MOCK_JOB = {
    "id": "ashby-1",
    "title": "Data Engineer",
    "jobUrl": "https://jobs.ashbyhq.com/testco/1",
    "location": {"name": "Islamabad, Pakistan"},
    "employmentType": "Full-time",
    "departmentName": "Data",
    "descriptionPlain": "Join our data team.",
    "publishedAt": "2024-02-01T12:00:00Z",
    "compensation": {
        "compensationTierSummary": "$60,000 - $90,000",
    },
}

def _next_html(listings):
    import json
    data = {
        "props": {
            "pageProps": {
                "jobIndexData": {
                    "listings": listings,
                    "filters": {
                        "locations": [
                            {"id": 0, "text": "Remote"},
                            {"id": 1, "text": "San Francisco, CA"},
                        ],
                        "teams": [
                            {"id": 0, "text": "Engineering"},
                        ],
                        "tags": [],
                        "employmentTypes": [
                            {"id": 0, "text": "Full-time"},
                        ],
                    },
                }
            }
        }
    }
    return f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(data)}</script>'


class TestCompanyConfig:
    def test_required_fields(self) -> None:
        config = CompanyConfig(
            name="TestCo",
            platform="greenhouse",
            careers_url="https://boards.greenhouse.io/testco",
        )
        assert config.name == "TestCo"
        assert config.platform == "greenhouse"
        assert config.skip is False
        assert config.api_key is None
        assert config.locations is None

    def test_optional_fields(self) -> None:
        config = CompanyConfig(
            name="TestCo",
            platform="ashby",
            careers_url="https://jobs.ashbyhq.com/testco",
            api_key="test-key",
            locations=["Islamabad"],
            skip=True,
        )
        assert config.api_key == "test-key"
        assert config.locations == ["Islamabad"]
        assert config.skip is True


class TestGreenhouseAdapter:
    GH_COMPANY = CompanyConfig(
        name="TestCo",
        platform="greenhouse",
        careers_url="https://boards.greenhouse.io/testco",
    )

    @pytest.mark.asyncio
    async def test_fetch_remix(self) -> None:
        adapter = GreenhouseAdapter()
        html = _remix_html([GH_MOCK_JOB])
        with patch.object(adapter.http, "get", AsyncMock(return_value=html)):
            result = await adapter.fetch(self.GH_COMPANY)
            assert len(result) == 1
            assert result[0]["title"] == "Backend Engineer"

    @pytest.mark.asyncio
    async def test_fetch_nextjs(self) -> None:
        adapter = GreenhouseAdapter()
        listings = [
            {
                "greenhouseId": 1,
                "title": "Next.js Engineer",
                "slug": "nextjs-engineer",
                "locationIndices": [0],
                "teamIndices": [0],
                "tagIndices": [],
                "employmentTypeIndex": 0,
            }
        ]
        html = _next_html(listings)
        with patch.object(adapter.http, "get", AsyncMock(return_value=html)):
            result = await adapter.fetch(self.GH_COMPANY)
            assert len(result) == 1
            assert result[0]["title"] == "Next.js Engineer"
            assert "Remote" in str(result[0].get("location", ""))

    @pytest.mark.asyncio
    async def test_fetch_no_data(self) -> None:
        adapter = GreenhouseAdapter()
        with patch.object(adapter.http, "get", AsyncMock(return_value="<html></html>")):
            result = await adapter.fetch(self.GH_COMPANY)
            assert result == []

    @pytest.mark.asyncio
    async def test_parse_extracts_fields(self) -> None:
        adapter = GreenhouseAdapter()
        parsed = await adapter.parse([GH_MOCK_JOB], self.GH_COMPANY)
        assert len(parsed) == 1
        job = parsed[0]
        assert isinstance(job, RawJob)
        assert job.title == "Backend Engineer"
        assert job.company == "TestCo"
        assert job.location == "Remote"
        assert job.source == "greenhouse"
        assert job.source_id == "gh-TestCo-12345"
        assert job.remote_type == "remote"
        assert job.is_remote is True

    @pytest.mark.asyncio
    async def test_parse_extracts_metadata(self) -> None:
        adapter = GreenhouseAdapter()
        parsed = await adapter.parse([GH_MOCK_JOB], self.GH_COMPANY)
        assert parsed[0].employment_type == "Full-time"
        assert parsed[0].experience_level == "Senior"

    @pytest.mark.asyncio
    async def test_parse_onsite_location(self) -> None:
        adapter = GreenhouseAdapter()
        onsite_job = dict(GH_MOCK_JOB, location={"name": "Islamabad, Pakistan"})
        parsed = await adapter.parse([onsite_job], self.GH_COMPANY)
        assert parsed[0].remote_type == "onsite"

    @pytest.mark.asyncio
    async def test_parse_nextjs_job(self) -> None:
        adapter = GreenhouseAdapter()
        nextjs_job = {
            "id": "2",
            "greenhouseId": 2,
            "title": "Frontend Developer",
            "absolute_url": "https://boards.greenhouse.io/testco/jobs/frontend",
            "location": "San Francisco, CA",
            "team": "Engineering",
            "employmentType": "Full-time",
            "updatedAt": "2024-03-01",
        }
        parsed = await adapter.parse([nextjs_job], self.GH_COMPANY)
        assert len(parsed) == 1
        assert parsed[0].title == "Frontend Developer"
        assert parsed[0].source_id == "gh-TestCo-2"


class TestLeverAdapter:
    LEVER_COMPANY = CompanyConfig(
        name="TestCo",
        platform="lever",
        careers_url="https://api.lever.co/v0/postings/testco",
    )

    @pytest.mark.asyncio
    async def test_fetch_calls_api(self) -> None:
        adapter = LeverAdapter()
        with patch.object(
            adapter.http, "get_json", AsyncMock(return_value=[LEVER_MOCK_JOB])
        ) as mock_get:
            result = await adapter.fetch(self.LEVER_COMPANY)
            assert len(result) == 1
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_parse_extracts_fields(self) -> None:
        adapter = LeverAdapter()
        parsed = await adapter.parse([LEVER_MOCK_JOB], self.LEVER_COMPANY)
        assert len(parsed) == 1
        job = parsed[0]
        assert job.title == "Software Engineer"
        assert job.company == "TestCo"
        assert job.location == "Remote"
        assert job.source == "lever"
        assert job.source_id == "lever-TestCo-abc-def"
        assert job.remote_type == "remote"
        assert job.employment_type == "Full-time"
        assert job.experience_level == "Engineering"

    @pytest.mark.asyncio
    async def test_parse_salary(self) -> None:
        adapter = LeverAdapter()
        parsed = await adapter.parse([LEVER_MOCK_JOB], self.LEVER_COMPANY)
        assert parsed[0].salary_min == 60000.0
        assert parsed[0].salary_max == 90000.0
        assert parsed[0].currency == "USD"

    @pytest.mark.asyncio
    async def test_fetch_derives_slug_from_url(self) -> None:
        adapter = LeverAdapter()
        company = CompanyConfig(
            name="Arbisoft",
            platform="lever",
            careers_url="https://jobs.lever.co/testco",
        )
        with patch.object(adapter.http, "get_json", AsyncMock(return_value=[LEVER_MOCK_JOB])):
            result = await adapter.fetch(company)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_fetch_handles_error(self) -> None:
        adapter = LeverAdapter()
        with patch.object(adapter.http, "get_json", AsyncMock(side_effect=Exception("down"))):
            result = await adapter.fetch(self.LEVER_COMPANY)
            assert result == []


class TestAshbyAdapter:
    ASHBY_COMPANY = CompanyConfig(
        name="TestCo",
        platform="ashby",
        careers_url="https://jobs.ashbyhq.com/testco",
        api_key="test-api-key",
    )

    @pytest.mark.asyncio
    async def test_fetch_requires_api_key(self) -> None:
        adapter = AshbyAdapter()
        company_no_key = CompanyConfig(
            name="NoKeyCo",
            platform="ashby",
            careers_url="https://jobs.ashbyhq.com/nokey",
        )
        with patch.object(adapter.http, "get_json", AsyncMock()) as mock_get:
            result = await adapter.fetch(company_no_key)
            assert result == []
            mock_get.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_calls_api_with_key(self) -> None:
        adapter = AshbyAdapter()
        with patch.object(
            adapter.http,
            "get_json",
            AsyncMock(return_value={"jobs": [ASHBY_MOCK_JOB]}),
        ) as mock_get:
            result = await adapter.fetch(self.ASHBY_COMPANY)
            assert len(result) == 1
            mock_get.assert_called_once_with(
                "https://api.ashbyhq.com/posting-api/job-board/test-api-key"
            )

    @pytest.mark.asyncio
    async def test_parse_extracts_fields(self) -> None:
        adapter = AshbyAdapter()
        parsed = await adapter.parse([ASHBY_MOCK_JOB], self.ASHBY_COMPANY)
        assert len(parsed) == 1
        job = parsed[0]
        assert job.title == "Data Engineer"
        assert job.company == "TestCo"
        assert job.source == "ashby"
        assert job.source_id == "ashby-TestCo-ashby-1"
        assert job.employment_type == "Full-time"
        assert job.experience_level == "Data"

    @pytest.mark.asyncio
    async def test_parse_compensation(self) -> None:
        adapter = AshbyAdapter()
        parsed = await adapter.parse([ASHBY_MOCK_JOB], self.ASHBY_COMPANY)
        assert parsed[0].salary_min == 60000.0
        assert parsed[0].salary_max == 90000.0
        assert parsed[0].currency == "USD"


class TestRemixExtraction:
    def test_extracts_jobs(self) -> None:
        html = _remix_html([GH_MOCK_JOB])
        result = _extract_remix_jobs(html, "testco")
        assert len(result) == 1
        assert result[0]["title"] == "Backend Engineer"

    def test_no_context_returns_empty(self) -> None:
        assert _extract_remix_jobs("<html></html>", "testco") == []

    def test_invalid_json_returns_empty(self) -> None:
        html = '<script>window.__remixContext = {invalid};</script>'
        assert _extract_remix_jobs(html, "testco") == []


class TestNextJSExtraction:
    def test_extracts_jobs_with_lookups(self) -> None:
        listings = [
            {
                "greenhouseId": 42,
                "title": "API Developer",
                "slug": "api-dev",
                "locationIndices": [1],
                "teamIndices": [0],
                "tagIndices": [],
                "employmentTypeIndex": 0,
            }
        ]
        html = _next_html(listings)
        result = _extract_next_jobs(html, "testco")
        assert len(result) == 1
        job = result[0]
        assert job["title"] == "API Developer"
        assert "San Francisco" in str(job.get("location", ""))
        assert job.get("team") == "Engineering"

    def test_no_next_data_returns_empty(self) -> None:
        assert _extract_next_jobs("<html></html>", "testco") == []

    def test_invalid_json_returns_empty(self) -> None:
        html = '<script id="__NEXT_DATA__" type="application/json">{bad</script>'
        assert _extract_next_jobs(html, "testco") == []

    def test_empty_listings(self) -> None:
        html = _next_html([])
        result = _extract_next_jobs(html, "testco")
        assert result == []
