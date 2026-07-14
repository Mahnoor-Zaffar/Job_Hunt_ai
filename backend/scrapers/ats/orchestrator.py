import asyncio
import logging
from typing import Any

from backend.scrapers.ats.adapter import BaseATSAdapter
from backend.scrapers.ats.ashby import AshbyAdapter
from backend.scrapers.ats.companies import CompanyConfig, load_companies
from backend.scrapers.ats.greenhouse import GreenhouseAdapter
from backend.scrapers.ats.lever import LeverAdapter
from backend.scrapers.ats.workable import WorkableAdapter
from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.models.models import RawJob
from backend.scrapers.registry.registry import register

logger = logging.getLogger("job_hunting.ats.orchestrator")

_ADAPTER_REGISTRY: dict[str, type[BaseATSAdapter]] = {
    "greenhouse": GreenhouseAdapter,
    "lever": LeverAdapter,
    "ashby": AshbyAdapter,
    "workable": WorkableAdapter,
}


@register(
    "ats",
    display_name="ATS Platforms (Greenhouse, Lever, Ashby, Workable)",
    locations=["Pakistan", "Remote"],
    interval=60,
)
class ATSOrchestrator(BaseScraper):
    """Meta-scraper that dispatches company configurations to ATS adapters.

    Reads ``companies.yaml``, groups entries by platform, instantiates
    the matching adapter, and aggregates all discovered jobs into a
    single :class:`NormalizedJob` list.  Adding a company requires no
    code changes — just a line in the YAML config.
    """

    source = "ats"

    async def fetch(self) -> list[tuple[CompanyConfig, list[dict[str, Any]]]]:
        companies = load_companies()
        if not companies:
            logger.warning("No companies configured for ATS scraping")
            return []

        groups: dict[str, list[CompanyConfig]] = {}
        for c in companies:
            groups.setdefault(c.platform, []).append(c)

        results: list[tuple[CompanyConfig, list[dict[str, Any]]]] = []

        for platform, entries in groups.items():
            adapter_cls = _ADAPTER_REGISTRY.get(platform)
            if adapter_cls is None:
                logger.warning("No adapter for platform '%s' — skipping", platform)
                continue

            adapter = adapter_cls(http_client=self.http)

            tasks = []
            for entry in entries:
                tasks.append(self._fetch_one(adapter, entry))

            batch = await asyncio.gather(*tasks, return_exceptions=True)
            for item in batch:
                if isinstance(item, BaseException):
                    logger.error("ATS fetch failed: %s", item)
                else:
                    results.append(item)

            await adapter.close()

        return results

    async def parse(self, raw: Any) -> list[RawJob]:
        items: list[tuple[CompanyConfig, list[dict[str, Any]]]] = (
            raw if isinstance(raw, list) else []
        )
        all_jobs: list[RawJob] = []

        groups: dict[str, list[tuple[CompanyConfig, list[dict[str, Any]]]]] = {}
        for company, data in items:
            groups.setdefault(company.platform, []).append((company, data))

        for platform, entries in groups.items():
            adapter_cls = _ADAPTER_REGISTRY.get(platform)
            if adapter_cls is None:
                continue

            adapter = adapter_cls(http_client=self.http)

            tasks = []
            for company, data in entries:
                tasks.append(self._parse_one(adapter, data, company))

            batch = await asyncio.gather(*tasks, return_exceptions=True)
            for item in batch:
                if isinstance(item, BaseException):
                    logger.error("ATS parse failed: %s", item)
                else:
                    all_jobs.extend(item)

            await adapter.close()

        logger.info(
            "ATS orchestrator parsed %d jobs across %d companies", len(all_jobs), len(items)
        )
        return all_jobs

    async def _fetch_one(
        self,
        adapter: BaseATSAdapter,
        company: CompanyConfig,
    ) -> tuple[CompanyConfig, list[dict[str, Any]]]:
        logger.debug("Fetching %s with %s adapter", company.name, adapter.platform)
        raw = await adapter.fetch(company)
        logger.debug("Fetched %d jobs from %s", len(raw), company.name)
        return company, raw

    async def _parse_one(
        self,
        adapter: BaseATSAdapter,
        raw: list[dict[str, Any]],
        company: CompanyConfig,
    ) -> list[RawJob]:
        return await adapter.parse(raw, company)
