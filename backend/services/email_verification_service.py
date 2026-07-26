"""Background service that periodically verifies HR emails for companies."""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.repositories.company import CompanyRepository

logger = logging.getLogger("job_hunting.email_verify")


class EmailVerificationService:
    """Periodically picks unverified companies and validates their HR emails."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = session_factory
        self._running = False

    async def run_cycle(self) -> int:
        """Verify up to 10 companies per cycle. Returns number verified."""
        async with self._factory() as session:
            repo = CompanyRepository(session)
            companies = await repo.get_unverified(limit=10)

        if not companies:
            return 0

        verified_count = 0
        for company in companies:
            try:
                ok = await self._verify_one(company)
                if ok:
                    verified_count += 1
            except Exception:
                logger.exception("Email verification failed for %s", company.name)

            await asyncio.sleep(2)

        if verified_count:
            logger.info("Verified emails for %d companies", verified_count)
        return verified_count

    async def _verify_one(self, company) -> bool:
        from urllib.parse import urlparse

        from backend.automation.email_validator import validate_emails_for_domain

        if not company.website:
            return False

        domain = urlparse(company.website).netloc.replace("www.", "")
        if not domain:
            return False

        guessed = [
            {"email": f"hr@{domain}", "priority": 2, "label": "HR Department"},
            {"email": f"careers@{domain}", "priority": 3, "label": "Jobs/Careers"},
            {"email": f"jobs@{domain}", "priority": 3, "label": "Jobs/Careers"},
        ]

        try:
            validated = await asyncio.wait_for(
                validate_emails_for_domain(domain, guessed),
                timeout=30,
            )
        except TimeoutError:
            logger.debug("Timeout verifying %s (%s)", company.name, domain)
            return False

        best: dict | None = None
        for v in validated:
            conf = v.get("confidence", 0)
            if conf >= 50 and (best is None or conf > best.get("confidence", 0)):
                best = v

        if best:
            async with self._factory() as session:
                repo = CompanyRepository(session)
                await repo.update_hr_email(
                    company_id=company.id,
                    email=best["email"],
                    confidence=best.get("confidence", 50),
                    source=best.get("source", "unknown"),
                )
                await session.commit()
            return True

        return False

    async def verify_single(self, company_id) -> dict | None:
        """Verify a single company on demand. Returns the best email info or None."""
        async with self._factory() as session:
            repo = CompanyRepository(session)
            company = await repo.get_by_id(company_id)

        if not company:
            return None

        ok = await self._verify_one(company)
        if ok:
            async with self._factory() as session:
                repo = CompanyRepository(session)
                company = await repo.get_by_id(company_id)
                return {
                    "hr_email": company.hr_email,
                    "hr_email_confidence": company.hr_email_confidence,
                    "hr_email_source": company.hr_email_source,
                    "hr_email_verified_at": company.hr_email_verified_at,
                }
        return None

    async def run_loop(self, interval: int = 1800) -> None:
        """Run verification cycles every `interval` seconds (default 30 min)."""
        self._running = True
        logger.info("Email verification background loop started (interval=%ds)", interval)
        while self._running:
            try:
                await self.run_cycle()
            except Exception:
                logger.exception("Email verification cycle failed")
            await asyncio.sleep(interval)
