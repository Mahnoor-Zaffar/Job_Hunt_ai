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
    industry: str = ""
    size: str = ""
    linkedin: str = ""
    scanned: bool = False


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

        return sorted(
            targets,
            key=lambda c: (0 if c.tier == "Tier 1" else 1 if c.tier == "Tier 2" else 2, c.name),
        )

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

                links = re.findall(
                    r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                    content,
                    re.DOTALL,
                )
                for href, title_html in links:
                    name = re.sub(r"<[^>]+>", "", title_html).strip()
                    if not name or len(name) < 3 or len(name) > 80:
                        continue
                    if any(
                        w in name.lower()
                        for w in ["wikipedia", "linkedin", "crunchbase", "youtube"]
                    ):
                        continue
                    domain = self._extract_domain(href)
                    if not domain or domain in self._seen_domains:
                        continue
                    self._seen_domains.add(domain)
                    if name not in results:
                        results[name] = CompanyResult(
                            name=name, website=f"https://{domain}", city=city
                        )
            except Exception:
                continue

        if len(results) < 5:
            await self._fallback_discovery(results)

        return list(results.values())

    async def _fallback_discovery(self, results: dict[str, CompanyResult]) -> None:
        known = [
            ("DealCart", "dealcart.pk", "Karachi", "E-commerce", "10-25", "dealcart"),
            ("PriceOye", "priceoye.pk", "Islamabad", "E-commerce", "30-50", "priceoye"),
            ("Markaz", "markaz.app", "Islamabad", "E-commerce", "20-40", "markazapp"),
            ("Byte", "byte.pk", "Lahore", "E-commerce", "10-25", "bytepk"),
            ("Tajir", "tajir.com", "Lahore", "E-commerce", "30-60", "tajir"),
            ("Krave Mart", "kravemart.com", "Karachi", "E-commerce", "50-80", "kravemart"),
            ("Sastaticket", "sastaticket.pk", "Karachi", "Travel", "30-50", "sastaticketpk"),
            ("Rider", "rider.pk", "Karachi", "E-commerce", "40-70", "riderpk"),
            ("CreditBook", "creditbook.pk", "Karachi", "Fintech", "40-60", "creditbookpk"),
            ("Udhaar App", "udhaar.app", "Karachi", "Fintech", "20-40", "udhaarapp"),
            ("QistBazaar", "qistbazaar.pk", "Karachi", "Fintech", "20-40", "qistbazaar"),
            ("Haball", "haball.com", "Karachi", "Fintech", "20-40", "haball"),
            ("AdalFi", "adalfi.com", "Lahore", "Fintech", "15-30", "adalfi"),
            ("Aamarpay", "aamarpay.com", "Karachi", "Fintech", "15-30", "aamarpay"),
            ("Mahaana Wealth", "mahaana.com", "Islamabad", "Fintech", "10-20", "mahaanawith"),
            ("SadaPay", "sadapay.co", "Islamabad", "Fintech", "50-80", "sadapay"),
            ("NayaPay", "nayapay.com", "Islamabad", "Fintech", "80-120", "nayapay"),
            ("Abhi", "abhi.com.pk", "Karachi", "Fintech", "60-100", "abhi-pk"),
            ("QisstPay", "qisstpay.com", "Islamabad", "Fintech", "30-50", "qisstpay"),
            ("OneLoad", "oneload.com", "Islamabad", "Fintech", "30-50", "oneload"),
            ("Elphinstone", "elphinstone.co", "Karachi", "Fintech", "10-20", "elphinstonefin"),
            ("Tag", "tag.co", "Karachi", "Fintech", "20-40", "tagpk"),
            ("Dbank", "dbank.pk", "Lahore", "Fintech", "40-60", "dbank-pk"),
            ("Marham", "marham.pk", "Lahore", "HealthTech", "30-50", "marhampk"),
            ("Oladoc", "oladoc.com", "Lahore", "HealthTech", "40-60", "oladoc"),
            ("MedIQ", "mediq.com.pk", "Lahore", "HealthTech", "20-40", "mediqpk"),
            ("Xylexa", "xylexa.com", "Karachi", "HealthTech", "10-20", "xylexa"),
            ("MedznMore", "medznmore.com", "Karachi", "HealthTech", "15-30", "medznmore"),
            ("Sehat Kahani", "sehatkahani.com", "Karachi", "HealthTech", "30-50", "sehat-kahani"),
            ("Maqsad", "maqsad.pk", "Karachi", "EdTech", "30-60", "maqsadpk"),
            ("Edkasa", "edkasa.com", "Lahore", "EdTech", "15-30", "edkasa"),
            ("Myco", "myco.io", "Karachi", "EdTech", "20-40", "mycoapp"),
            ("Atomcamp", "atomcamp.com", "Islamabad", "EdTech", "15-30", "atomcamp"),
            ("Knowledge Platform", "knowledgeplatform.com", "Islamabad", "EdTech", "40-60", "knowledge-platform"),
            ("Hunarza", "hunarza.com", "Karachi", "EdTech", "5-15", "hunarza"),
            ("Revora AI", "revora.ai", "Karachi", "AI/ML", "10-20", "revoraai"),
            ("Oware", "oware.tech", "Karachi", "AI/ML", "10-20", "owaretech"),
            ("Uplift AI", "upliftaiorg", "Karachi", "Voice AI", "10-20", "upliftaiorg"),
            ("Zypl AI", "zypl.ai", "Karachi", "AI/ML", "15-30", "zyplai"),
            ("Vyro AI", "vyro.ai", "Karachi", "AI/ML", "30-50", "vyroai"),
            ("Vector AI", "vector-ai.co", "Sialkot", "AI/ML", "10-20", "vectoraico"),
            ("Dastgyr", "dastgyr.com", "Karachi", "B2B Commerce", "60-100", "dastgyr"),
            ("Savyour", "savyour.com", "Karachi", "B2B Commerce", "20-40", "savyourpk"),
            ("Zaraye", "zaraye.pk", "Karachi", "B2B Marketplace", "15-25", "zarayepk"),
            ("Retailo", "retailo.com", "Karachi", "B2B Commerce", "60-100", "retailo"),
            ("Bazaar Technologies", "bazaar.tech", "Karachi", "B2B Commerce", "80-120", "bazaar-technologies"),
            ("PostEx", "postex.pk", "Karachi", "Logistics", "50-80", "postexpk"),
            ("Truck It In", "truckitin.com", "Karachi", "Logistics", "30-50", "truckitin"),
            ("Trukkr", "trukkr.com", "Karachi", "Logistics", "10-20", "trukkr"),
            ("BridgeLinx", "bridgelinx.com", "Karachi", "Logistics", "30-50", "bridgelinx"),
            ("Cheetay", "cheetay.pk", "Karachi", "Logistics", "40-60", "cheetaypk"),
            ("Rover", "rover.pk", "Lahore", "Logistics", "20-40", "roverpk"),
            ("Convo", "convoz.com", "Lahore", "SaaS", "40-60", "convoz"),
            ("COLABS", "colabs.pk", "Lahore", "SaaS", "20-40", "colabspk"),
            ("Ease", "ease.xyz", "Karachi", "SaaS", "10-20", "easexyz"),
            ("SMMGuro", "smmguro.com", "Karachi", "SaaS", "15-30", "smmguro"),
            ("EventMobi", "eventmobi.com", "Lahore", "SaaS", "50-80", "eventmobi"),
            ("BusCaro", "buscaro.com", "Karachi", "Mobility", "20-40", "buscaro"),
            ("Bookme", "bookme.pk", "Islamabad", "Travel", "40-60", "bookmepk"),
            ("Bykea", "bykea.com", "Karachi", "Mobility", "60-100", "bykea"),
            ("CarFirst", "carfirst.com", "Karachi", "Auto", "40-60", "carfirstpk"),
            ("Gaadi", "gaadi.pk", "Lahore", "Auto", "15-25", "gaadipk"),
            ("Zyp Technologies", "zyp.tech", "Karachi", "EV", "20-40", "zyptech"),
            ("E-Vehicle", "e-vehicle.pk", "Lahore", "EV", "10-20", "evehiclepk"),
            ("Roomy", "roomy.pk", "Karachi", "PropTech", "10-20", "roomypk"),
            ("Haveli", "haveli.pk", "Lahore", "PropTech", "10-20", "havelipk"),
            ("VaporVM", "vaporvm.com", "Lahore", "Cloud", "30-50", "vaporvm"),
            ("TekRevol", "tekrevol.com", "Lahore", "Software", "60-100", "tekrevol"),
            ("BitSol", "bitsol.com", "Lahore", "Software", "20-40", "bitsol"),
            ("MyAdvo", "myadvo.pk", "Karachi", "LegalTech", "10-20", "myadvo"),
            ("Shopy", "shopy.pk", "Lahore", "E-commerce", "10-20", "shopy"),
            ("TaxCorp", "taxcorp.pk", "Karachi", "Fintech", "10-20", "taxcorp"),
            ("PakWheels", "pakwheels.com", "Karachi", "Auto", "80-150", "pakwheels"),
            ("Youth Club", "youthclub.pk", "Karachi", "EdTech", "15-25", "youthclubpk"),
            ("Techling", "techling.pk", "Lahore", "Software", "10-20", "techlingpk"),
                "Lahore",
                "Venture Capital",
                "10-30",
                "fatima-ventures",
            ),
            ("Zindigi", "zindigi.com", "Islamabad", "Fintech", "100-300", "zindigi"),
        ]
        for name, domain, city, industry, size, linkedin_slug in known:
            if name not in results:
                results[name] = CompanyResult(
                    name=name,
                    website=f"https://{domain}",
                    city=city,
                    industry=industry,
                    size=size,
                    linkedin=f"https://linkedin.com/company/{linkedin_slug}",
                )
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
                company.website = (
                    f"https://{re.sub(r'[^a-z0-9]', '', company.name.lower())[:20]}.com"
                )

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
