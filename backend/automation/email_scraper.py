"""HR Email Scraper — finds recruiter/HR emails for job applications.

Uses Playwright to visit job pages, company websites, and Google
search results.  Extracts and prioritizes emails using regex.
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

logger = logging.getLogger("job_hunting.email_scraper")

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
)

HR_EMAIL_PREFIXES = {
    "hr",
    "careers",
    "career",
    "jobs",
    "recruiting",
    "recruitment",
    "talent",
    "people",
    "hiring",
}

CONTACT_PAGES = [
    "/about",
    "/about-us",
    "/contact",
    "/contact-us",
    "/careers",
    "/career",
    "/team",
    "/people",
]


@dataclass
class EmailResult:
    email: str
    source: str = ""
    priority: int = 5  # 1=best, 5=generic
    context: str = ""

    @property
    def priority_label(self) -> str:
        labels = {
            1: "Named HR/Recruiter",
            2: "HR Department",
            3: "Jobs/Careers",
            4: "Company",
            5: "Generic",
        }
        return labels.get(self.priority, "Generic")


class EmailScraper:
    def __init__(self, page: Any) -> None:
        self._page = page
        self._found: dict[str, EmailResult] = {}

    async def find_emails(
        self, job_url: str, company_name: str = "", company_url: str = ""
    ) -> list[EmailResult]:
        self._found = {}

        # Tier 1: Job page
        logger.debug("Tier 1: scanning job page %s", job_url[:60])
        await self._scan_page(job_url, "job_page")

        # Tier 2: Company homepage
        if company_url and company_url not in self._visited_urls():
            base = urljoin(company_url, "/")
            logger.debug("Tier 2: scanning company homepage %s", base[:60])
            await self._scan_page(base, "company_homepage")

        # Tier 3: Contact pages
        if company_url:
            base = urljoin(company_url, "/").rstrip("/")
            for path in CONTACT_PAGES:
                url = f"{base}{path}"
                if url not in self._visited_urls():
                    await self._scan_page(url, "contact_page")
                    await asyncio.sleep(0.5)

        # Tier 4: Google search
        if not self._has_good_email() and company_name:
            logger.debug("Tier 4: Google search for %s", company_name)
            await self._google_search(company_name)

        # Always add domain guesses as fallback if nothing good found
        if not self._has_good_email():
            self._add_domain_guesses(company_name, company_url or "")

        return self._prioritized()

    def _visited_urls(self) -> set[str]:
        return {r.source for r in self._found.values() if r.source}

    def _has_good_email(self) -> bool:
        return any(r.priority <= 3 for r in self._found.values())

    async def _scan_page(self, url: str, source_label: str) -> None:
        try:
            await self._page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(1)
            content = await self._page.content()
            text = await self._page.evaluate("() => document.body.innerText")
            self._extract_emails(content, text, url, source_label)
        except Exception as exc:
            logger.debug("Failed to scan %s: %s", url[:60], exc)

    async def _google_search(self, company_name: str) -> None:
        query = f"{company_name} careers hr email contact"
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        try:
            await self._page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(2)
            content = await self._page.content()
            text = await self._page.evaluate("() => document.body.innerText")
            self._extract_emails(content, text, search_url, "google_search")
        except Exception as exc:
            logger.debug("Google search failed: %s", exc)

    def _extract_emails(self, html: str, text: str, source: str, label: str) -> None:
        seen = set(self._found.keys())
        for match in EMAIL_PATTERN.finditer(html + " " + text):
            email = match.group(0).lower().strip()
            if email in seen or "example" in email or "test" in email:
                continue
            seen.add(email)

            start = max(0, match.start() - 60)
            end = min(len(html), match.end() + 60)
            context = html[start:end].replace("\n", " ").strip()

            priority = self._classify_priority(email, context)
            self._found[email] = EmailResult(
                email=email,
                source=label,
                priority=priority,
                context=context[:120],
            )

    def _classify_priority(self, email: str, context: str) -> int:
        local = email.split("@")[0].lower()

        if any(p in local for p in HR_EMAIL_PREFIXES):
            return 2 if local in HR_EMAIL_PREFIXES else 3

        named_patterns = [
            r"[a-z]+\.[a-z]+@",
            r"(john|sarah|mike|lisa|emma|james|anna|david|kate|chris|alex)\b",
        ]
        for pattern in named_patterns:
            if re.search(pattern, email):
                return 1

        if any(kw in context.lower() for kw in ["recruiter", "hr", "hiring", "talent acquisition"]):
            return 2

        generic = {"info", "contact", "hello", "support", "admin", "office", "team"}
        if local in generic:
            return 5

        return 4

    def _prioritized(self) -> list[EmailResult]:
        results = sorted(self._found.values(), key=lambda r: r.priority)
        return results

    def _add_domain_guesses(self, company_name: str, company_url: str) -> None:
        domain = ""
        try:
            parsed = urlparse(company_url)
            domain = parsed.netloc.replace("www.", "")
        except Exception:
            pass

        if domain:
            for prefix, prio in [("hr", 3), ("careers", 3), ("jobs", 3), ("recruiting", 3), ("info", 5)]:
                guess = f"{prefix}@{domain}"
                if guess not in self._found:
                    self._found[guess] = EmailResult(email=guess, source="domain_guess", priority=prio, context=f"Generated from {domain}")
        elif company_name:
            clean = re.sub(r"[^a-z0-9]", "", company_name.lower())[:20]
            if clean:
                for prefix, prio in [("hr", 4), ("careers", 4), ("info", 5)]:
                    guess = f"{prefix}@{clean}.com"
                    if guess not in self._found:
                        self._found[guess] = EmailResult(email=guess, source="domain_guess", priority=prio, context=f"Generated from {company_name}")
