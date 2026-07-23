"""Pakistan Startup Discovery — finds companies, detects remote roles, discovers HR emails.

Phases:
  1. DuckDuckGo search → extract company names + websites + cities
  2. Per-company role + remote detection via website scanning
  3. HR email discovery via domain-guess fallback
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
    "Islamabad": "Islamabad OR Rawalpindi",
    "Lahore": "Lahore",
    "Karachi": "Karachi",
}

SEARCH_QUERIES = [
    "{city} software startups 2025 2026",
    "{city} tech companies remote developers",
    "{city} startups raised funding 2025",
    "{city} IT companies careers",
    "{city} SaaS companies",
    "{city} tech startups hiring",
]

NATIONAL_QUERIES = [
    "Pakistan tech startups 2026 Y Combinator",
    "Pakistani startups remote full-stack developer",
    "Pakistan software companies remote work 2026",
]

ROLE_KEYWORDS = [
    "full-stack", "fullstack", "full stack", "backend", "back-end",
    "frontend", "front-end", "software engineer", "developer",
    "python", "javascript", "react", "node.js", "nodejs",
    "fastapi", "django", "typescript", "go", "rust", "flutter",
]

REMOTE_KEYWORDS = [
    "remote", "work from home", "wfh", "anywhere",
    "distributed team", "remote-first", "work remotely",
    "global team", "remote position", "fully remote",
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
        self._seen_domains: set[str] = set()

    async def discover(
        self, *, max_companies: int = 60, scan_depth: int = 3
    ) -> list[CompanyResult]:
        logger.info("Phase 1: Discovering companies via search engines")
        companies = await self._discover_companies()

        logger.info("Phase 2: Role detection for %d companies (quick scan)", len(companies))
        sem = asyncio.Semaphore(3)
        targets = companies[:max_companies]
        tasks = [self._scan_company(c, sem) for c in targets[:15]]
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("Phase 3: Email discovery for all companies")
        self._run_email_scraper(targets)

        return sorted(targets, key=lambda c: (0 if c.tier == "Tier 1" else 1 if c.tier == "Tier 2" else 2, c.name))

    async def _discover_companies(self) -> list[CompanyResult]:
        results: dict[str, CompanyResult] = {}

        queries: list[tuple[str, str]] = []
        for city_display, city_query in CITIES.items():
            for template in SEARCH_QUERIES:
                queries.append((template.format(city=city_query), city_display))
        for q in NATIONAL_QUERIES:
            queries.append((q, "Pakistan"))

        for query, city in queries:
            try:
                url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
                await self._page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(0.3)
                content = await self._page.content()

                links = re.findall(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', content, re.DOTALL)
                for href, title_html in links:
                    name = re.sub(r"<[^>]+>", "", title_html).strip()
                    if not name or len(name) < 3 or len(name) > 80:
                        continue
                    if any(w in name.lower() for w in ["wikipedia", "linkedin", "crunchbase", "youtube"]):
                        continue
                    domain = self._extract_domain(href)
                    if not domain or domain in self._seen_domains:
                        continue
                    self._seen_domains.add(domain)
                    if name not in results:
                        results[name] = CompanyResult(name=name, website=f"https://{domain}", city=city)
            except Exception:
                continue

        if len(results) < 5:
            await self._fallback_discovery(results)

        return list(results.values())

    async def _fallback_discovery(self, results: dict[str, CompanyResult]) -> None:
        """Hardcoded fallback: known Pakistani tech companies."""
        known = [
            ("SadaPay", "sadapay.co", "Karachi"),
            ("Bazaar Technologies", "bazaar.tech", "Karachi"),
            ("Dbank", "dbank.pk", "Lahore"),
            ("NayaPay", "nayapay.com", "Islamabad"),
            ("Tajir", "tajir.com", "Lahore"),
            ("Airlift", "airlifttech.com", "Lahore"),
            ("KTrade", "ktrade.pk", "Karachi"),
            ("PostEx", "postex.com", "Lahore"),
            ("Abhi", "abhi.com.pk", "Karachi"),
            ("QisstPay", "qisstpay.com", "Islamabad"),
            ("OneLoad", "oneload.com", "Islamabad"),
            ("DealCart", "dealcart.io", "Karachi"),
            ("Retailo", "retailo.com", "Karachi"),
            ("Dastgyr", "dastgyr.com", "Lahore"),
            ("MediBuddy Pakistan", "medibuddy.pk", "Karachi"),
            ("CreditBook", "creditbook.pk", "Karachi"),
            ("Truck It In", "truckitin.com", "Karachi"),
            ("PriceOye", "priceoye.pk", "Lahore"),
            ("Savyour", "savyour.com", "Karachi"),
            ("Atomcamp", "atomcamp.com", "Islamabad"),
            ("VentureDive", "venturedive.com", "Lahore"),
            ("Arbisoft", "arbisoft.com", "Lahore"),
            ("Confiz", "confiz.com", "Lahore"),
            ("Devsinc", "devsinc.com", "Lahore"),
            ("Systems Ltd", "systemsltd.com", "Lahore"),
            ("Techlogix", "techlogix.com", "Lahore"),
            ("10Pearls", "10pearls.com", "Karachi"),
            ("Folio3", "folio3.com", "Karachi"),
            ("Contour Software", "contour-software.com", "Karachi"),
            ("i2c Inc", "i2cinc.com", "Lahore"),
            ("Careem", "careem.com", "Karachi"),
            ("Motive", "gomotive.com", "Islamabad"),
            ("KeepTruckin Pakistan", "keeptruckin.com", "Islamabad"),
            ("Afiniti", "afiniti.com", "Karachi"),
            ("TeraData Pakistan", "teradata.com", "Islamabad"),
            ("Dubizzle Labs", "dubizzlelabs.com", "Lahore"),
            ("Gaditek", "gaditek.com", "Karachi"),
            ("Seven Technologies", "seventech.com.pk", "Islamabad"),
            ("Techlogix Pakistan", "techlogix.com", "Lahore"),
            ("ePlanet Communications", "eplanetcom.com", "Lahore"),
            ("Next Generation Innovations", "ngi.com.pk", "Islamabad"),
            ("SDSol Technologies", "sdsol.com", "Lahore"),
            ("VaporVM", "vaporvm.com", "Lahore"),
            ("Code for Pakistan", "codeforpakistan.org", "Islamabad"),
            ("PITB", "pitb.gov.pk", "Lahore"),
            ("Ignite National Technology Fund", "ignite.org.pk", "Islamabad"),
            ("PlanX", "planx.pk", "Lahore"),
            ("The Nest I/O", "thenest.io", "Karachi"),
            ("Telenor Velocity", "telenorvelocity.com", "Islamabad"),
            ("Jazz xlr8", "jazzxlr8.com", "Islamabad"),
        ]
        for name, domain, city in known:
            if name not in results:
                results[name] = CompanyResult(name=name, website=f"https://{domain}", city=city)
        logger.info("Fallback: added %d known companies", len(known))

    def _extract_domain(self, url: str) -> str:
        with suppress(Exception):
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            if domain and "." in domain and len(domain) > 5:
                return domain
            if parsed.path:
                clean = parsed.path.strip("/").split("/")[0]
                if "." in clean:
                    return clean.replace("www.", "")
        return ""

    async def _scan_company(self, company: CompanyResult, sem: asyncio.Semaphore) -> None:
        async with sem:
            if not company.website:
                company.website = f"https://{re.sub(r'[^a-z0-9]', '', company.name.lower())[:20]}.com"

            pages = [company.website]
            base = company.website.rstrip("/")
            for path in ["/careers", "/jobs", "/about", "/career"]:
                pages.append(f"{base}{path}")

            for page_url in pages[:2]:
                try:
                    await self._page.goto(page_url, wait_until="domcontentloaded", timeout=8000)
                    await asyncio.sleep(0.2)
                    text = await self._page.evaluate("() => document.body.innerText")
                    text_lower = text.lower()

                    roles = [kw for kw in ROLE_KEYWORDS if kw in text_lower]
                    if roles:
                        company.hiring = True
                        company.roles_found = list(set(roles))[:5]

                        for role in roles:
                            idx = text_lower.find(role)
                            if idx > 0:
                                company.requirements = text[max(0, idx - 50):idx + 300].strip()
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

    def _run_email_scraper(self, companies: list[CompanyResult]) -> None:
        for c in companies:
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
            ]:
                emails.append({"email": f"{prefix}@{domain}", "priority": prio, "label": label})
            c.emails = emails

            c.email_keywords = {
                "suggested_subject": f"Full-Stack Developer — {'Remote' if c.remote else 'On-site'} — {c.city}",
                "subject_kw": ["full-stack", "developer", c.city.lower()],
                "body_kw": ["Python", "JavaScript", "React", "Node.js", "TypeScript", "Docker"],
            }
