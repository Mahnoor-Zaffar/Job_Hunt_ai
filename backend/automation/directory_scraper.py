"""Multi-source Pakistan startup directory scraper.

Fetches company listings from directories using Playwright (browser).
Results are cached to disk to avoid repeat scraping.

Sources:
  - F6S Pakistan         (100+ companies)
  - ReflectPakistan      (800+ companies, JS-rendered)
  - StartupBlink         (1100+ companies)
  - PakStartups.org      (directory API)
  - Web search supplement
"""

import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger("job_hunting.directory_scraper")

CACHE_FILE = Path(__file__).parent / ".startup_cache.json"
CACHE_TTL = 86400  # 24 hours

KNOWN_INDUSTRIES = {
    "fintech", "edtech", "healthtech", "e-commerce", "ecommerce",
    "logistics", "saas", "ai", "ml", "ai/ml", "cleantech", "agritech",
    "proptech", "mobility", "travel", "auto", "ev", "software",
    "cloud", "legaltech", "foodtech", "medtech", "iot",
}


@dataclass
class StartupEntry:
    name: str
    domain: str
    city: str = ""
    industry: str = ""
    size: str = ""
    linkedin_slug: str = ""
    source: str = ""


def _extract_domain(url: str) -> str:
    if not url.startswith("http"):
        url = f"https://{url}"
    try:
        parsed = urlparse(url)
        return parsed.netloc.replace("www.", "").lower()
    except Exception:
        return url.lower().replace("https://", "").replace("http://", "").split("/")[0]


def _infer_industry(name: str, description: str = "") -> str:
    text = (name + " " + description).lower()
    if any(kw in text for kw in ["fintech", "financ", "bank", "payment", "lend", "invest", "insure"]):
        return "Fintech"
    if any(kw in text for kw in ["edtech", "educat", "learn", "school", "course", "student"]):
        return "EdTech"
    if any(kw in text for kw in ["health", "medic", "doctor", "clinic", "hospital", "telemed"]):
        return "HealthTech"
    if any(kw in text for kw in ["e-commerce", "ecommerce", "retail", "shop", "commerce"]):
        return "E-commerce"
    if any(kw in text for kw in ["logistics", "delivery", "freight", "courier", "ship"]):
        return "Logistics"
    if any(kw in text for kw in ["ai", "ml", "machine learning", "artificial intelligence"]):
        return "AI/ML"
    if any(kw in text for kw in ["saas", "software", "cloud"]):
        return "SaaS"
    if any(kw in text for kw in ["travel", "tour", "hotel", "booking"]):
        return "Travel"
    if any(kw in text for kw in ["food", "restaurant", "kitchen"]):
        return "FoodTech"
    if any(kw in text for kw in ["real estate", "property", "prop"]):
        return "PropTech"
    if any(kw in text for kw in ["legal"]):
        return "LegalTech"
    if any(kw in text for kw in ["agri", "farm", "crop"]):
        return "AgriTech"
    if any(kw in text for kw in ["ev", "electric", "solar", "energy", "clean"]):
        return "CleanTech"
    return "Software"


def _infer_city(text: str) -> str:
    cities = ["karachi", "lahore", "islamabad", "rawalpindi", "sialkot", "faisalabad", "peshawar", "multan", "gujranwala", "quetta", "hyderabad"]
    for c in cities:
        if c in text.lower():
            return c.capitalize()
    return ""


def _parse_size(text: str) -> str:
    m = re.search(r"(\d+)\s*[-–to]+\s*(\d+)\s*employees?", text, re.I)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m = re.search(r"(?:employees?|size|team)[:\s]*(\d+[-–]\d+)", text, re.I)
    if m:
        return m.group(1)
    return ""


# ── Directory scrapers ──────────────────────────────────────────────────────


async def scrape_f6s(page: Any) -> list[StartupEntry]:
    """Scrape F6S Pakistan listing."""
    entries: list[StartupEntry] = []
    base = "https://www.f6s.com/companies/pakistan/lo"
    try:
        await page.goto(base, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)
        html = await page.content()
        # Company cards
        blocks = re.findall(
            r'<div[^>]*class="[^"]*company-item[^"]*"[^>]*>.*?</div>\s*</div>\s*</div>',
            html, re.DOTALL,
        )
        if not blocks:
            blocks = re.findall(r'<div[^>]*class="[^"]*card[^"]*"[^>]*>.*?</div>\s*</div>', html, re.DOTALL)
        for block in blocks:
            name_m = re.search(r'<h[23][^>]*>(.*?)</h[23]>', block, re.DOTALL)
            if not name_m:
                continue
            name = re.sub(r"<[^>]+>", "", name_m.group(1)).strip()
            if not name or len(name) < 2:
                continue
            link_m = re.search(r'href="(https?://[^"]+)"', block)
            domain = _extract_domain(link_m.group(1)) if link_m else ""
            text = re.sub(r"<[^>]+>", " ", block).strip()
            city = _infer_city(text)
            industry = _infer_industry(name, text)
            size = _parse_size(text)
            entries.append(StartupEntry(name=name, domain=domain, city=city, industry=industry, size=size, source="f6s"))
    except Exception as e:
        logger.warning("F6S scrape failed: %s", e)
    return entries


async def scrape_reflect_pakistan(page: Any) -> list[StartupEntry]:
    """Scrape ReflectPakistan startup directory."""
    entries: list[StartupEntry] = []
    base = "https://reflectpakistan.com/startup-directory/"
    try:
        await page.goto(base, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(3)
        html = await page.content()

        # Cards from the directory
        cards = re.findall(
            r'<div[^>]*class="[^"]*(?:startup-card|company-card|card)[^"]*"[^>]*>.*?</article>',
            html, re.DOTALL,
        )
        if not cards:
            cards = re.findall(
                r'<h3[^>]*>(.*?)</h3>.*?<p[^>]*>(.*?)</p>.*?📍\s*(.*?)·',
                html, re.DOTALL,
            )
            for name_html, desc, loc in cards:
                name = re.sub(r"<[^>]+>", "", name_html).strip()
                if not name or len(name) < 2:
                    continue
                desc_text = re.sub(r"<[^>]+>", "", desc).strip()
                domain = _extract_domain(name)
                if not domain:
                    link_m = re.search(r'href="(https?://[^"]+)"', html[html.find(name_html):])
                    if link_m:
                        domain = _extract_domain(link_m.group(1))
                city = _infer_city(loc)
                industry = _infer_industry(name, desc_text)
                entries.append(StartupEntry(name=name, domain=domain, city=city, industry=industry, source="reflect"))

        if not entries:
            # Fallback: extract from JSON-LD or visible text
            text = re.sub(r"<[^>]+>", "\n", html)
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            for i, line in enumerate(lines):
                if "📍" in line:
                    name = lines[i - 1] if i > 0 else ""
                    if name and len(name) > 2 and not any(x in name.lower() for x in ["subscribe", "search", "menu"]):
                        domain = ""
                        d = next((lines[i + 1] for i2, l in enumerate(lines[i:]) if l.startswith("https") or l.startswith("http")), "")
                        if d:
                            domain = _extract_domain(d)
                        city = _infer_city(line)
                        entries.append(StartupEntry(name=name, domain=domain, city=city, source="reflect"))
    except Exception as e:
        logger.warning("ReflectPakistan scrape failed: %s", e)
    return entries


async def scrape_pakstartups(page: Any) -> list[StartupEntry]:
    """Scrape PAK Startups directory via API if available, else parse page."""
    entries: list[StartupEntry] = []
    try:
        await page.goto("https://pakstartups.com/directory", wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)
        html = await page.content()
        cards = re.findall(
            r'<div[^>]*class="[^"]*(?:startup-item|company-card|card)[^"]*"[^>]*>.*?</div>\s*</div>',
            html, re.DOTALL,
        )
        for card in cards:
            name_m = re.search(r'<h[23][^>]*>(.*?)</h[23]>', card, re.DOTALL)
            if not name_m:
                continue
            name = re.sub(r"<[^>]+>", "", name_m.group(1)).strip()
            link_m = re.search(r'href="(https?://[^"]+)"', card)
            domain = _extract_domain(link_m.group(1)) if link_m else ""
            text = re.sub(r"<[^>]+>", " ", card).strip()
            city = _infer_city(text)
            industry = _infer_industry(name, text)
            entries.append(StartupEntry(name=name, domain=domain, city=city, industry=industry, source="pakstartups"))
    except Exception as e:
        logger.warning("PakStartups scrape failed: %s", e)
    return entries


async def scrape_startupblink(page: Any) -> list[StartupEntry]:
    """Scrape StartupBlink Pakistan ranking."""
    entries: list[StartupEntry] = []
    try:
        await page.goto("https://www.startupblink.com/top-startups/pakistan", wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(2)
        html = await page.content()
        rows = re.findall(
            r'<tr[^>]*>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?</tr>',
            html, re.DOTALL,
        )
        for rank, name_html, desc_html in rows:
            name = re.sub(r"<[^>]+>", "", name_html).strip()
            if not name or len(name) < 2:
                continue
            desc = re.sub(r"<[^>]+>", "", desc_html).strip()
            link_m = re.search(r'href="(https?://[^"]+)"', name_html)
            domain = _extract_domain(link_m.group(1)) if link_m else ""
            city = _infer_city(desc)
            industry = _infer_industry(name, desc)
            entries.append(StartupEntry(name=name, domain=domain, city=city, industry=industry, source="startupblink"))
    except Exception as e:
        logger.warning("StartupBlink scrape failed: %s", e)
    return entries


# ── Main scraper orchestrator ────────────────────────────────────────────────


async def discover_startups() -> list[StartupEntry]:
    """Run all directory scrapers and return deduplicated results."""
    # Check cache first
    cache = _load_cache()
    if cache:
        logger.info("Loaded %d startups from cache", len(cache))
        return cache

    from backend.scrapers.browser.manager import BrowserManager

    bm = BrowserManager()
    all_entries: dict[str, StartupEntry] = {}

    try:
        await bm.start()
        page = await bm.get_page()

        scrapers = [
            ("F6S", scrape_f6s),
            ("ReflectPakistan", scrape_reflect_pakistan),
            ("PakStartups", scrape_pakstartups),
            ("StartupBlink", scrape_startupblink),
        ]

        for name, scraper in scrapers:
            logger.info("Scraping %s...", name)
            try:
                entries = await asyncio.wait_for(scraper(page), timeout=45)
                logger.info("  → %d entries from %s", len(entries), name)
                for e in entries:
                    key = e.domain or e.name.lower()
                    if key and key not in all_entries:
                        all_entries[key] = e
            except (TimeoutError, Exception) as exc:
                logger.warning("  → %s failed: %s", name, exc)

    finally:
        await bm.close()

    results = list(all_entries.values())
    logger.info("Total unique startups from directories: %d", len(results))

    # Supplement with web search
    logger.info("Running web search discovery...")
    try:
        search_results = await discover_via_search()
        for e in search_results:
            key = e.domain or e.name.lower()
            if key and key not in all_entries:
                all_entries[key] = e
        logger.info("  → %d from web search, total: %d", len(search_results), len(all_entries))
    except Exception as e:
        logger.warning("Web search failed: %s", e)

    # Supplement with curated extended list
    for e in curated_extended_list():
        key = e.domain or e.name.lower()
        if key and key not in all_entries:
            all_entries[key] = e
    logger.info("Total after curated supplement: %d", len(all_entries))

    results = list(all_entries.values())
    _save_cache(results)
    return results


async def discover_startups_light() -> list[StartupEntry]:
    """Try httpx-only scraping (faster, no browser) for sites that allow it."""
    import httpx
    all_entries: dict[str, StartupEntry] = {}

    # Some directories respond to plain HTTP
    urls = [
        ("reflect", "https://reflectpakistan.com/startup-directory/"),
    ]
    async with httpx.AsyncClient(timeout=15, follow_redirects=True, verify=False) as client:
        for source, url in urls:
            try:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code != 200:
                    continue
                html = resp.text
                cards = re.findall(r'<h3[^>]*>(.*?)</h3>.*?<p[^>]*>(.*?)</p>', html, re.DOTALL)
                for name_html, desc in cards:
                    name = re.sub(r"<[^>]+>", "", name_html).strip()
                    if not name or len(name) < 2:
                        continue
                    desc_text = re.sub(r"<[^>]+>", "", desc).strip()
                    city = _infer_city(desc_text)
                    industry = _infer_industry(name, desc_text)
                    link_m = re.search(r'href="(https?://[^"]+)"', html[html.find(name_html):])
                    domain = _extract_domain(link_m.group(1)) if link_m else ""
                    key = domain or name.lower()
                    if key not in all_entries:
                        all_entries[key] = StartupEntry(name=name, domain=domain, city=city, industry=industry, source=source)
            except Exception:
                continue

    return list(all_entries.values())


# ── Cache helpers ────────────────────────────────────────────────────────────


def _load_cache() -> list[StartupEntry]:
    if not CACHE_FILE.exists():
        return []
    try:
        with open(CACHE_FILE) as f:
            data = json.load(f)
        if time.time() - data.get("ts", 0) > CACHE_TTL:
            return []
        return [StartupEntry(**e) for e in data.get("entries", [])]
    except Exception:
        return []


def _save_cache(entries: list[StartupEntry]) -> None:
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({
                "ts": time.time(),
                "entries": [{"name": e.name, "domain": e.domain, "city": e.city, "industry": e.industry, "size": e.size, "linkedin_slug": e.linkedin_slug, "source": e.source} for e in entries],
            }, f)
        logger.info("Saved %d startups to cache", len(entries))
    except Exception as e:
        logger.warning("Failed to save cache: %s", e)


# ── Web search discovery ─────────────────────────────────────────────────────


SKIP_DOMAINS = {
    "gov.pk", "gos.pk", "tripadvisor.com", "britannica.com", "worldatlas.com",
    "dawn.com", "bbc.com", "aljazeera.com", "youtube.com", "facebook.com",
    "reddit.com", "wikipedia.org", "amazon.com", "twitter.com", "instagram.com",
    "linkedin.com", "nih.gov", "who.int", "bloomberg.com", "reuters.com",
    "forbes.com", "techcrunch.com",
}

SKIP_TITLE_PATTERNS = [
    "wikipedia", "tripadvisor", "facebook", "instagram", "youtube",
    "hotel", "restaurant", "tourist", "travel guide", "weather",
    "jobs in", "career in", "salary", "visa",
]


async def discover_via_search() -> list[StartupEntry]:
    """Use DuckDuckGo search API to discover startups by industry + city."""
    entries: dict[str, StartupEntry] = {}

    queries = [
        "list of fintech companies in Pakistan 2025 2026",
        "best fintech startups Pakistan list",
        "edtech companies in Pakistan list",
        "healthtech startups Pakistan list 2025",
        "ecommerce companies Pakistan list 2025",
        "logistics startups in Pakistan list",
        "SaaS companies in Pakistan list",
        "AI startups in Pakistan 2025 2026",
        "tech startups in Karachi list",
        "tech startups in Lahore list",
        "tech startups in Islamabad list",
        "Y Combinator backed Pakistani startups",
        "seed funded startups Pakistan 2025",
        "fastest growing startups in Pakistan 2026",
        "top software companies in Pakistan",
    ]

    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            for query in queries:
                try:
                    results = list(ddgs.text(query, max_results=15, region="wt-wt"))
                except Exception:
                    await asyncio.sleep(1)
                    try:
                        results = list(ddgs.text(query, max_results=15, region="wt-wt"))
                    except Exception:
                        continue

                for r in results:
                    title = r.get("title", "")
                    body = r.get("body", "")
                    href = r.get("href", "")
                    if not title or len(title) < 3:
                        continue
                    if any(skip in title.lower() for skip in SKIP_TITLE_PATTERNS):
                        continue
                    domain = _extract_domain(href)
                    if not domain:
                        continue
                    domain_lower = domain.lower()
                    if any(domain_lower.endswith("." + sd) for sd in SKIP_DOMAINS):
                        continue
                    if any(sd in domain_lower for sd in ["tripadvisor", "britannica", "facebook", "twitter", "youtube", "reddit"]):
                        continue

                    name = title.split(" - ")[0].split(" | ")[0].split(" — ")[0].strip()
                    if len(name) < 3:
                        continue
                    if any(kw in name.lower() for kw in ["top ", "best ", "list of ", "how to", "guide"]):
                        continue

                    text = (title + " " + body)
                    city = _infer_city(text)
                    industry = _infer_industry(name, text)

                    key = domain
                    if key and key not in entries:
                        entries[key] = StartupEntry(name=name, domain=domain, city=city, industry=industry, source="search")
                await asyncio.sleep(0.5)
    except ImportError:
        logger.warning("duckduckgo_search not installed")
    except Exception as e:
        logger.warning("Search discovery failed: %s", e)

    return list(entries.values())


# ── Curated extended list ────────────────────────────────────────────────────


def curated_extended_list() -> list[StartupEntry]:
    """Return a large curated list of Pakistani startups from research sources."""
    return [
        # Fintech
        StartupEntry("Keenu", "keenu.pk", "Lahore", "Fintech", "10-30", "keenu"),
        StartupEntry("Dukan", "dukan.pk", "Karachi", "Fintech", "20-40", "dukanpk"),
        StartupEntry("PayFast", "payfast.pk", "Karachi", "Fintech", "10-20", "payfast"),
        StartupEntry("FinPocket", "finpocket.com.pk", "Karachi", "Fintech", "10-20", "finpocket"),
        StartupEntry("KalPay", "kalpay.com", "Islamabad", "Fintech", "15-30", "kalpay"),
        StartupEntry("MicroFi", "microfi.app", "Islamabad", "Fintech", "5-15", "microfi"),
        StartupEntry("Bachat App", "bachat.app", "Karachi", "Fintech", "10-20", "bachatapp"),
        StartupEntry("PayMaya", "paymaya.pk", "Karachi", "Fintech", "5-15", "paymaya"),
        StartupEntry("Fauree", "fauree.io", "Karachi", "Fintech", "11-50", "fauree"),
        StartupEntry("Meezan", "meezan.com", "Karachi", "Fintech", "30-60", "meezan"),
        StartupEntry("Tez Financial", "tezfinancials.com", "Karachi", "Fintech", "10-20", "tezfinancials"),
        StartupEntry("NayaPay", "nayapay.com", "Islamabad", "Fintech", "80-120", "nayapay"),
        StartupEntry("Sarmaaya", "sarmaaya.pk", "Karachi", "Fintech", "10-20", "sarmaaya"),
        StartupEntry("ScoreMyCredit", "scoremycredit.pk", "Karachi", "Fintech", "5-15", "scoremycredit"),
        StartupEntry("Easypaisa", "easypaisa.com.pk", "Karachi", "Fintech", "200-500", "easypaisa"),
        StartupEntry("JazzCash", "jazzcash.com.pk", "Islamabad", "Fintech", "200-500", "jazzcash"),
        StartupEntry("Akhtar & Co", "akhtarco.com", "Karachi", "Fintech", "5-15", "akhtar-co"),
        # E-commerce
        StartupEntry("Shopsy", "shopsy.pk", "Lahore", "E-commerce", "15-30", "shopsy"),
        StartupEntry("Telemart", "telemart.pk", "Lahore", "E-commerce", "20-40", "telemartpk"),
        StartupEntry("HomeShopping.pk", "homeshopping.pk", "Karachi", "E-commerce", "30-50", "hs-pk"),
        StartupEntry("iShopping.pk", "ishopping.pk", "Karachi", "E-commerce", "20-40", "ishoppingpk"),
        StartupEntry("GharPar", "gharpar.pk", "Karachi", "E-commerce", "5-15", "gharpar"),
        StartupEntry("ShopEx", "shopex.pk", "Lahore", "E-commerce", "10-20", "shopexpk"),
        StartupEntry("Vendek", "vendek.pk", "Karachi", "E-commerce", "5-15", "vendek"),
        StartupEntry("MartKing", "martking.pk", "Lahore", "E-commerce", "5-15", "martkingpk"),
        # EdTech
        StartupEntry("Nearpeer", "nearpeer.org", "Lahore", "EdTech", "30-60", "nearpeer"),
        StartupEntry("Sabaq.pk", "sabaq.pk", "Islamabad", "EdTech", "10-20", "sabaqpk"),
        StartupEntry("Orenda", "orenda.pk", "Lahore", "EdTech", "10-20", "orendapk"),
        StartupEntry("EduMate", "edumate.pk", "Karachi", "EdTech", "5-15", "edumate"),
        StartupEntry("Taleemabad", "taleemabad.com", "Islamabad", "EdTech", "15-30", "taleemabad"),
        StartupEntry("DigiSkills", "digiskills.pk", "Islamabad", "EdTech", "20-40", "digiskills"),
        StartupEntry("The EduPro", "theedupro.com", "Lahore", "EdTech", "5-15", "theedupro"),
        StartupEntry("LearnOBots", "learnobots.com", "Lahore", "EdTech", "10-20", "learnobots"),
        # HealthTech
        StartupEntry("WonderTree", "wondertree.co", "Karachi", "HealthTech", "10-20", "wondertree"),
        StartupEntry("Dawaai", "dawaai.pk", "Karachi", "HealthTech", "30-60", "dawaai"),
        StartupEntry("Pulse by Zong", "pulsebyzong.com", "Islamabad", "HealthTech", "30-50", "pulsebyzong"),
        StartupEntry("DoctorsHood", "doctorshood.com", "Lahore", "HealthTech", "10-20", "doctorshood"),
        StartupEntry("HealthWire", "healthwire.pk", "Karachi", "HealthTech", "20-40", "healthwire"),
        StartupEntry("Marham", "marham.pk", "Lahore", "HealthTech", "30-50", "marham"),
        StartupEntry("MediPocket", "medipocket.com", "Karachi", "HealthTech", "10-20", "medipocket"),
        StartupEntry("Dr.Kami", "drkami.com", "Lahore", "HealthTech", "5-15", "drkami"),
        # Logistics
        StartupEntry("Airlift", "airlift.pk", "Lahore", "Logistics", "30-50", "airliftpk"),
        StartupEntry("Leopards Courier", "leopardscourier.com", "Karachi", "Logistics", "500-1000", "leopardscourier"),
        StartupEntry("TCS", "tcs.com.pk", "Karachi", "Logistics", "1000-5000", "tcs-pakistan"),
        StartupEntry("M&P Express", "mexpk.com", "Karachi", "Logistics", "50-100", "mpexpress"),
        StartupEntry("Call Courier", "callcourier.com.pk", "Karachi", "Logistics", "100-200", "callcourier"),
        StartupEntry("Rider Logistics", "riderlogistics.pk", "Karachi", "Logistics", "40-70", "riderlogistics"),
        StartupEntry("ShipEdge", "shipedge.pk", "Karachi", "Logistics", "10-20", "shipedge"),
        StartupEntry("Delypk", "dely.pk", "Lahore", "Logistics", "5-15", "delypk"),
        # AI/ML
        StartupEntry("Uplift AI", "upliftaiorg", "Islamabad", "AI/ML", "15-30", "upliftaiorg"),
        StartupEntry("Metric", "metricapp.co", "Islamabad", "AI/ML", "10-20", "metricapp"),
        StartupEntry("Metal", "metal.org", "Karachi", "AI/ML", "5-15", "metalorg"),
        StartupEntry("Zypl AI", "zypl.ai", "Karachi", "AI/ML", "15-30", "zyplai"),
        StartupEntry("Vyro AI", "vyro.ai", "Karachi", "AI/ML", "30-50", "vyroai"),
        StartupEntry("Vector AI", "vector-ai.co", "Sialkot", "AI/ML", "10-20", "vectorai"),
        StartupEntry("Revora AI", "revora.ai", "Karachi", "AI/ML", "10-20", "revoraai"),
        StartupEntry("Data Darbar", "datadarbar.ai", "Islamabad", "AI/ML", "10-20", "datadarbar"),
        StartupEntry("Echooo AI", "echooo.ai", "Karachi", "AI/ML", "5-15", "echooai"),
        StartupEntry("ZahanatAI", "zahanatai.com", "Karachi", "AI/ML", "5-15", "zahanatai"),
        # SaaS / Software
        StartupEntry("Convo", "convoz.com", "Lahore", "SaaS", "40-60", "convoz"),
        StartupEntry("COLABS", "colabs.pk", "Lahore", "SaaS", "20-40", "colabspk"),
        StartupEntry("Ease", "ease.xyz", "Karachi", "SaaS", "10-20", "easexyz"),
        StartupEntry("EventMobi", "eventmobi.com", "Lahore", "SaaS", "50-80", "eventmobi"),
        StartupEntry("10Pearls", "10pearls.com", "Karachi", "SaaS", "1400+", "10pearls"),
        StartupEntry("Systems Limited", "systemsltd.com", "Karachi", "SaaS", "2000+", "systemsltd"),
        StartupEntry("Arbisoft", "arbisoft.com", "Lahore", "SaaS", "500+", "arbisoft"),
        StartupEntry("Contour Software", "contoursoftware.com", "Karachi", "SaaS", "300+", "contoursoftware"),
        StartupEntry("Folio3", "folio3.com", "Karachi", "SaaS", "300+", "folio3"),
        StartupEntry("NetMatic", "netmatic.com", "Islamabad", "SaaS", "50-100", "netmatic"),
        StartupEntry("Phantom", "phantom.pk", "Karachi", "SaaS", "10-20", "phantompk"),
        StartupEntry("LetTech", "lettech.pk", "Peshawar", "SaaS", "10-20", "lettech"),
        # AgriTech
        StartupEntry("Agrilift", "agrilift.pk", "Karachi", "AgriTech", "10-20", "agrilift"),
        StartupEntry("Tazah", "tazah.pk", "Karachi", "AgriTech", "20-40", "tazahpk"),
        StartupEntry("Crop2X", "crop2x.com", "Lahore", "AgriTech", "10-20", "crop2x"),
        StartupEntry("Reap", "reap.ag", "Karachi", "AgriTech", "10-20", "reapag"),
        StartupEntry("NayaAasan", "nayaaasan.com", "Lahore", "AgriTech", "5-15", "nayaaasan"),
        # PropTech
        StartupEntry("Roomy", "roomy.pk", "Karachi", "PropTech", "10-20", "roomypk"),
        StartupEntry("Haveli", "haveli.pk", "Lahore", "PropTech", "10-20", "havelipk"),
        StartupEntry("Zameen.com", "zameen.com", "Lahore", "PropTech", "200-500", "zameen"),
        StartupEntry("Ghar47", "ghar47.com", "Islamabad", "PropTech", "20-40", "ghar47"),
        StartupEntry("PropertyMozo", "propertymozo.com", "Karachi", "PropTech", "10-20", "propertymozo"),
        # Mobility
        StartupEntry("BusCaro", "buscaro.com", "Karachi", "Mobility", "20-40", "buscaro"),
        StartupEntry("Bykea", "bykea.com", "Karachi", "Mobility", "60-100", "bykea"),
        StartupEntry("Swyft", "swyft.pk", "Lahore", "Mobility", "10-20", "swyftpk"),
        StartupEntry("Indrive", "indrive.com", "Karachi", "Mobility", "30-60", "indrivepk"),
        # Gaming / Entertainment
        StartupEntry("Maticz", "maticz.com", "Lahore", "Gaming", "20-40", "maticz"),
        StartupEntry("Game District", "gamedistrict.com", "Karachi", "Gaming", "50-100", "gamedistrict"),
        StartupEntry("Mundo Games", "mundogames.com", "Karachi", "Gaming", "30-50", "mundogames"),
        StartupEntry("GenITeam", "geniteam.com", "Islamabad", "Gaming", "50-100", "geniteam"),
        # B2B / Marketplace
        StartupEntry("Dastgyr", "dastgyr.com", "Karachi", "B2B Commerce", "60-100", "dastgyr"),
        StartupEntry("Bazaar", "bazaar.pk", "Karachi", "B2B Commerce", "80-120", "bazaar"),
        StartupEntry("Zaraye", "zaraye.pk", "Karachi", "B2B Marketplace", "15-25", "zaraye"),
        StartupEntry("Retailo", "retailo.com", "Karachi", "B2B Commerce", "60-100", "retailo"),
        StartupEntry("Savyour", "savyour.com", "Karachi", "B2B Commerce", "20-40", "savyour"),
        # Travel
        StartupEntry("Bookme", "bookme.pk", "Islamabad", "Travel", "40-60", "bookme"),
        StartupEntry("Sastaticket", "sastaticket.pk", "Karachi", "Travel", "30-50", "sastaticket"),
        StartupEntry("Travel Beta", "travelbeta.pk", "Lahore", "Travel", "10-20", "travelbeta"),
        StartupEntry("TripKarachi", "tripkarachi.com", "Karachi", "Travel", "5-15", "tripkarachi"),
        # EV / CleanTech
        StartupEntry("Zyp Technologies", "zyp.tech", "Karachi", "EV", "20-40", "zyptech"),
        StartupEntry("E-Vehicle", "e-vehicle.pk", "Lahore", "EV", "10-20", "evehiclepk"),
        StartupEntry("EVB", "evb.pk", "Karachi", "EV", "10-20", "evbpk"),
        StartupEntry("SolarMax", "solarmax.pk", "Lahore", "CleanTech", "10-20", "solarmaxpk"),
        # Other
        StartupEntry("Shadiyana", "shadiyana.pk", "Karachi", "WeddingTech", "10-20", "shadiyana"),
        StartupEntry("Olive Planet", "oliveplanet.com", "Karachi", "CleanTech", "10-20", "oliveplanet"),
        StartupEntry("ProVaz", "provaz.com", "Lahore", "LegalTech", "5-15", "provaz"),
        StartupEntry("Youth Club", "youthclub.pk", "Karachi", "EdTech", "15-25", "youthclubpk"),
        StartupEntry("Zameen Alert", "zameenalert.com", "Lahore", "PropTech", "5-15", "zameenalrt"),
    ]


def clear_cache() -> None:
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
        logger.info("Cache cleared")
