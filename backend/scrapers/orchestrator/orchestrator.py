import asyncio
import logging
import time
from decimal import Decimal

from backend.database.session import get_session_factory
from backend.models.job import Job
from backend.repositories.job import JobRepository
from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.browser.manager import BrowserManager
from backend.scrapers.config.config import ScraperSettings
from backend.scrapers.models.models import (
    ExecutionSummary,
    NormalizedJob,
    ScraperResult,
)
from backend.scrapers.registry.registry import ScraperRegistry

logger = logging.getLogger("job_hunting.orchestrator")


def _normalized_to_model(nj: NormalizedJob) -> Job:
    return Job(
        title=nj.title,
        company=nj.company,
        company_url=nj.company_url,
        location=nj.location,
        city=nj.city,
        country=nj.country,
        is_remote=nj.is_remote,
        remote_type=nj.remote_type,
        description=nj.description,
        requirements=nj.requirements,
        url=nj.url,
        apply_url=nj.apply_url,
        source=nj.source,
        source_id=nj.source_id,
        salary_min=Decimal(str(nj.salary_min)) if nj.salary_min is not None else None,
        salary_max=Decimal(str(nj.salary_max)) if nj.salary_max is not None else None,
        currency=nj.currency,
        employment_type=nj.employment_type,
        experience_level=nj.experience_level,
        skills=nj.skills,
        posted_at=nj.posted_at,
        expires_at=nj.expires_at,
        fingerprint=nj.fingerprint,
        status="active",
    )


class ScraperOrchestrator:
    """Coordinates the execution of registered scrapers.

    Launching, metrics collection, retries, and persistence are handled
    here so that individual scrapers remain focused on data extraction.
    """

    def __init__(
        self,
        registry: ScraperRegistry | None = None,
        settings: ScraperSettings | None = None,
        browser_manager: BrowserManager | None = None,
    ) -> None:
        self._registry = registry or ScraperRegistry()
        self._settings = settings or ScraperSettings()
        self._browser_manager = browser_manager or BrowserManager()

    async def run_all(self, sources: list[str] | None = None) -> ExecutionSummary:
        start = time.perf_counter()

        if sources:
            scraper_classes = [
                cls for src in sources if (cls := self._registry.get(src)) is not None
            ]
        else:
            scraper_classes = self._registry.get_enabled(self._settings)

        if not scraper_classes:
            logger.warning("No scrapers to run")
            return ExecutionSummary(
                total_scrapers=0,
                succeeded=0,
                failed=0,
                total_jobs=0,
                duration_seconds=0.0,
                results=[],
            )

        await self._browser_manager.start()

        semaphore = asyncio.Semaphore(self._settings.MAX_CONCURRENT)
        factory = get_session_factory()

        async def _run_one(cls: type[BaseScraper]) -> ScraperResult:
            async with semaphore:
                scraper = cls(settings=self._settings, browser_manager=self._browser_manager)
                job_start = time.perf_counter()
                try:
                    jobs = await scraper.scrape()
                    new_count = 0
                    async with factory() as session:
                        repo = JobRepository(session)
                        for nj in jobs:
                            existing = await repo.get_by_fingerprint(nj.fingerprint)
                            if existing is None:
                                model = _normalized_to_model(nj)
                                await repo.create(model)
                                new_count += 1
                        await session.flush()

                    duration = time.perf_counter() - job_start
                    logger.info(
                        "[%s] done — %d new jobs in %.2fs",
                        scraper.source,
                        new_count,
                        duration,
                    )
                    return ScraperResult(
                        source=scraper.source,
                        success=True,
                        jobs_found=new_count,
                        duration_seconds=duration,
                    )
                except Exception as exc:
                    duration = time.perf_counter() - job_start
                    logger.exception("[%s] failed after %.2fs", scraper.source, duration)
                    return ScraperResult(
                        source=scraper.source,
                        success=False,
                        jobs_found=0,
                        duration_seconds=duration,
                        error=str(exc),
                    )
                finally:
                    scraper.cleanup()

        results = await asyncio.gather(
            *[_run_one(cls) for cls in scraper_classes],
            return_exceptions=False,
        )

        total_duration = time.perf_counter() - start
        succeeded = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success)
        total_jobs = sum(r.jobs_found for r in results)

        summary = ExecutionSummary(
            total_scrapers=len(results),
            succeeded=succeeded,
            failed=failed,
            total_jobs=total_jobs,
            duration_seconds=total_duration,
            results=results,
        )

        logger.info(
            "Orchestrator finished: %d scrapers, %d succeeded, %d failed, %d jobs in %.2fs",
            summary.total_scrapers,
            summary.succeeded,
            summary.failed,
            summary.total_jobs,
            summary.duration_seconds,
        )
        return summary

    async def run_single(self, source: str) -> ScraperResult:
        cls = self._registry.get(source)
        if cls is None:
            return ScraperResult(
                source=source,
                success=False,
                jobs_found=0,
                duration_seconds=0.0,
                error=f"Unknown source: {source}",
            )
        return (await self.run_all(sources=[source])).results[0]
