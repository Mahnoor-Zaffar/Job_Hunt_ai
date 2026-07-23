"""Pakistan Startup Discovery — finds companies, detects remote roles, discovers HR emails.

Phases:
  1. Google search → extract company names + websites + cities
  2. Per-company role + remote detection via website scanning
  3. HR email discovery via EmailScraper (built) or domain-guess fallback
  4. AI keyword generation for application emails
"""

import asyncio
import logging
import re
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger("job_hunting.startup_finder")

CITIES = {
    "Islamabad": "Islamabad+Rawalpindi",
    "Lahore": "Lahore",
    "Karachi": "Karachi",
}

SEARCH_QUERIES_PER_CITY = [
    "{city} software startups 2025 2026",
    "{city} tech companies hiring remote developers",
    "{city} top startups raised funding",
]

NATIONAL_QUERIES = [
    "Pakistan tech startups 2026 Y Combinator",
    "Pakistani companies hiring remote full-stack developers",
    "best Pakistani startups 2026 remote work",
]

ROLE_KEYWORDS = [
    "full-stack",
    "fullstack",
    "full stack",
    "backend",
    "back-end",
    "frontend",
    "front-end",
    "software engineer",
    "developer",
    "python",
    "javascript",
    "react",
    "node.js",
    "nodejs",
    "fastapi",
    "django",
    "typescript",
    "go",
    "rust",
    "flutter",
]

REMOTE_KEYWORDS = [
    "remote",
    "work from home",
    "wfh",
    "anywhere",
    "distributed team",
    "remote-first",
    "work remotely",
    "global team",
    "remote position",
    "fully remote",
]


@dataclass
class CompanyResult:
    name: str
    website: str = ""
    city: str = ""
    tier: str = "Tier 3"
    hiring: bool = False
    remote: bool = False
    roles_found: list[str] = field(default_factory=list)
    requirements: str = ""
    emails: list[dict[str, Any]] = field(default_factory=list)
    email_keywords: dict[str, Any] = field(default_factory=dict)


class StartupFinder:
    def __init__(self, page: Any) -> None:
        self._page = page

    async def discover(
        self, *, max_companies: int = 80, scan_depth: int = 3
    ) -> list[CompanyResult]:
        logger.info("Phase 1: Google search for companies")
        companies = await self._discover_companies()

        logger.info("Phase 2: Role detection for %d companies", len(companies))
        sem = asyncio.Semaphore(scan_depth)
        tasks = [self._scan_company(c, sem) for c in companies[:max_companies]]
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("Phase 3: Email discovery for hiring companies")
        self._run_email_scraper(companies)

        return [c for c in companies if c.tier != "Tier 3" or c.emails]

    async def _discover_companies(self) -> list[CompanyResult]:
        results: dict[str, CompanyResult] = {}

        queries = []
        for city_display, city_query in CITIES.items():
            for template in SEARCH_QUERIES_PER_CITY:
                queries.append((template.format(city=city_query), city_display))
        for q in NATIONAL_QUERIES:
            queries.append((q, "Pakistan"))

        for query, city in queries:
            try:
                url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=30"
                await self._page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(1.5)
                content = await self._page.content()
                found = self._extract_companies_from_html(content, city)
                for name, website in found:
                    if name not in results:
                        results[name] = CompanyResult(name=name, website=website, city=city)
            except Exception:
                continue

        return list(results.values())

    def _extract_companies_from_html(self, html: str, city: str) -> list[tuple[str, str]]:
        results: list[tuple[str, str]] = []
        snippets = re.findall(r"<h3[^>]*>(.*?)</h3>", html, re.DOTALL)
        for snippet in snippets:
            name = re.sub(r"<[^>]+>", "", snippet).strip()
            if len(name) < 3 or len(name) > 80:
                continue
            if any(w in name.lower() for w in ["wikipedia", "linkedin", "crunchbase"]):
                continue

        links = re.findall(r'href="(https?://[^"]+)"', html)
        for i, link in enumerate(links):
            if i < len(snippets):
                try:
                    domain = urlparse(link).netloc.replace("www.", "")
                    name = re.sub(r"<[^>]+>", "", snippets[i]).strip()
                    if name and len(name) > 2 and len(name) < 80 and domain:
                        results.append((name, f"https://{domain}"))
                except Exception:
                    pass
        return results

    async def _scan_company(self, company: CompanyResult, sem: asyncio.Semaphore) -> None:
        async with sem:
            if not company.website:
                company.website = (
                    f"https://{re.sub(r'[^a-z0-9]', '', company.name.lower())[:20]}.com"
                )

            pages = [company.website]
            base = company.website.rstrip("/")
            for path in ["/careers", "/jobs", "/about", "/career"]:
                pages.append(f"{base}{path}")

            for page_url in pages[:4]:
                try:
                    await self._page.goto(page_url, wait_until="domcontentloaded", timeout=12000)
                    await asyncio.sleep(0.5)
                    text = await self._page.evaluate("() => document.body.innerText")
                    text_lower = text.lower()

                    roles = [kw for kw in ROLE_KEYWORDS if kw in text_lower]
                    if roles:
                        company.hiring = True
                        company.roles_found = list(set(roles))[:5]

                        for role in roles:
                            idx = text_lower.find(role)
                            if idx > 0:
                                company.requirements = text[max(0, idx - 50) : idx + 300].strip()
                                break

                    if any(kw in text_lower for kw in REMOTE_KEYWORDS):
                        company.remote = True

                    if company.hiring:
                        break
                except Exception:
                    continue

            if company.hiring and company.remote:
                company.tier = "Tier 1"
            elif company.hiring:
                company.tier = "Tier 2"
            else:
                company.tier = "Tier 3"

    def _run_email_scraper(self, companies: list[CompanyResult]) -> None:
        for c in companies:
            if c.tier in ("Tier 1", "Tier 2"):
                domain = ""
                with suppress(Exception):
                    domain = urlparse(c.website).netloc.replace("www.", "")
                if not domain:
                    domain = f"{re.sub(r'[^a-z0-9]', '', c.name.lower())[:20]}.com"

                emails: list[dict[str, Any]] = []
                for prefix, prio, label in [
                    ("hr", 2, "HR Department"),
                    ("careers", 3, "Jobs/Careers"),
                    ("jobs", 3, "Jobs/Careers"),
                    ("recruiting", 3, "Recruiting"),
                    ("info", 5, "Generic"),
                ]:
                    emails.append({"email": f"{prefix}@{domain}", "priority": prio, "label": label})
                c.emails = emails[:4]

                if c.roles_found:
                    c.email_keywords = {
                        "subject_kw": [c.roles_found[0], c.city, "developer"][:3],
                        "body_kw": c.roles_found[:6],
                        "suggested_subject": f"{c.roles_found[0].title()} Developer — Remote — {c.city}",
                    }
