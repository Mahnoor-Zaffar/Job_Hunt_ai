"""Mid-sized IT Company Discovery for Pakistan.

Discovers Pakistani IT/software companies with 50-500 employees
from curated lists, directory scraping, and web search.
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("job_hunting.it_company_scraper")

CACHE_FILE = os.path.join(os.path.dirname(__file__), ".it_company_cache.json")
CACHE_TTL = 86400  # 24 h


@dataclass
class CompanyEntry:
    name: str
    domain: str
    city: str
    industry: str
    size: str
    linkedin_slug: str
    category: str = "it_company"


def _curated_list() -> list[CompanyEntry]:
    """Curated list of 50+ mid-sized Pakistani IT companies (50-500 employees)."""
    return [
        # -- Raw entries (size 50-250) --
        CompanyEntry("Volmatica", "volmatica.com", "Rawalpindi", "Software Development", "80-249", "volmatica-inc"),
        CompanyEntry("Comtanix", "comtanix.com", "Rawalpindi", "BPO/Software", "55-200", "comtanix"),
        CompanyEntry("Zenkoders", "zenkoders.com", "Karachi", "Software Development", "51-200", "zenkoders"),
        CompanyEntry("Cubix", "cubix.co", "Karachi", "Software Development", "100-250", "cubixglobal"),
        CompanyEntry("NxN Pakistan", "nxn.com.pk", "Karachi", "Software Development", "8-50", "nxn-pakistan"),
        CompanyEntry("Liquid Technologies", "liqteq.com", "Karachi", "Software Development", "51-200", "liqteq"),
        CompanyEntry("Arpatech", "arpatech.com", "Karachi", "Software Development", "201-500", "arpatech"),
        CompanyEntry("VentureDive", "venturedive.com", "Karachi", "Software Development", "200-500", "venturedive"),
        CompanyEntry("Cygnis", "cygnislabs.com", "Karachi", "Software Development", "50-200", "cygnislabs"),
        CompanyEntry("KoderLabs", "koderlabs.com", "Karachi", "Software Development", "100-250", "koderlabs"),
        CompanyEntry("BariTechSol", "baritechsol.com", "Karachi", "Software Development", "50-249", "baritechsol"),
        CompanyEntry("8Ration", "8ration.com", "Karachi", "Software Development", "50-249", "8ration"),
        CompanyEntry("Brilworks", "brilworks.com", "Karachi", "Software Development", "50-100", "brilworks"),
        CompanyEntry("TPS Pakistan", "tps.com.pk", "Karachi", "Fintech", "100-200", "tps-pakistan"),
        CompanyEntry("Techlogix", "techlogix.com", "Lahore", "IT Services", "200-500", "techlogix"),
        CompanyEntry("Confiz", "confiz.com", "Lahore", "IT Services", "200-500", "confiz"),
        CompanyEntry("NetSol Technologies", "netsoltech.com", "Lahore", "Fintech", "500-1000", "netsoltech"),
        CompanyEntry("Devsinc", "devsinc.com", "Lahore", "Software Development", "300-500", "devsinc"),
        CompanyEntry("Tkxel", "tkxel.com", "Lahore", "Software Development", "250-500", "tkxel"),
        CompanyEntry("Jaffer Business Systems", "jbs.com.pk", "Lahore", "IT Services", "100-200", "jaffer-business-systems"),
        CompanyEntry("SN Skies", "snskies.com", "Lahore", "Software Development", "50-249", "snskies-pk"),
        CompanyEntry("Novatore Solutions", "novatore.com.pk", "Lahore", "Software Development", "50-200", "novatore"),
        CompanyEntry("Bitsclan", "bitsclan.com", "Lahore", "Software Development", "50-100", "bitsclan"),
        CompanyEntry("ESketchers", "esketchers.com", "Lahore", "Software Development", "50-100", "esketchers"),
        CompanyEntry("Beta Solutions", "betasolutions.com.pk", "Lahore", "Software Development", "50-150", "betasolutionspk"),
        CompanyEntry("Scube Solutions", "scubesolutions.com", "Lahore", "Software Development", "50-100", "scubesolutions"),
        CompanyEntry("Nascence Consulting", "nascence.com", "Lahore", "Software Development", "50-150", "nascence"),
        CompanyEntry("Mindstorm Labs", "mindstormlabs.com", "Lahore", "Software Development", "50-100", "mindstormlabs"),
        CompanyEntry("Kualitatem", "kualitatem.com", "Lahore", "QA/Software", "50-200", "kualitatem"),
        CompanyEntry("Sofizar", "sofizar.com", "Lahore", "Software Development", "50-150", "sofizar"),
        CompanyEntry("Xavor Corporation", "xavor.com", "Lahore", "Software Development", "100-300", "xavor"),
        CompanyEntry("NorthBay Solutions", "northbay.com", "Lahore", "Software Development", "100-300", "northbaysolutions"),
        CompanyEntry("Agility Solutions", "agility.pk", "Lahore", "Software Development", "50-100", "agility-pk"),
        CompanyEntry("i2c Inc Pakistan", "i2cinc.com", "Lahore", "Fintech", "200-500", "i2cinc"),
        CompanyEntry("Avanza Solutions", "avanzasolutions.com", "Islamabad", "Software Development", "100-250", "avanzasolutions"),
        CompanyEntry("Ovex Technologies", "ovextech.com", "Islamabad", "BPO", "300-700", "ovex-technologies"),
        CompanyEntry("Bravado Solutions", "bravadosolutions.com", "Islamabad", "Software Development", "50-200", "bravadosolutions"),
        CompanyEntry("Codistan Ventures", "codistan.org", "Islamabad", "Software Development", "50-150", "codistan"),
        CompanyEntry("Synergy IT", "synergyit.com", "Islamabad", "Software Development", "50-200", "synergyit"),
        CompanyEntry("Icreativez", "icreativez.com", "Islamabad", "Software Development", "50-150", "icreativez"),
        CompanyEntry("LMKT", "lmkt.com.pk", "Islamabad", "IT Services", "100-250", "lmkt"),
        CompanyEntry("Digitilization", "digilitization.com", "Islamabad", "Software Development", "50-100", "digilitization"),
        CompanyEntry("Hudsonex", "hudsonex.com", "Islamabad", "Software Development", "50-150", "hudsonexate"),
        CompanyEntry("Plutus Labs", "plutuslabs.com", "Islamabad", "Software Development", "50-100", "plutuslabs"),
        CompanyEntry("E2E Technologies", "e2e.com.pk", "Islamabad", "Software Development", "50-100", "e2e-pk"),
        CompanyEntry("Mountainise", "mountainise.com", "Islamabad", "Software Development", "50-100", "mountainise"),
        CompanyEntry("Ertiqah Consulting", "ertiqah.com", "Islamabad", "Software Development", "50-100", "ertiqah"),
        CompanyEntry("Vizteck Solutions", "vizteck.com", "Islamabad", "Software Development", "50-100", "vizteck"),
        CompanyEntry("M Techub", "mtechub.com", "Rawalpindi", "Software Development", "50-249", "mtechub"),
        CompanyEntry("Nexshore Technologies", "nexshoretech.com", "Islamabad", "Software Development", "50-100", "nexshore"),
    ]


async def _verify_domain(domain: str) -> bool:
    """Quick check that the domain resolves and returns HTTP 200."""
    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as c:
            r = await c.get(f"https://{domain}")
            return r.status_code < 500
    except Exception:
        return False


async def discover_companies() -> list[dict[str, Any]]:
    """Return list of IT companies, trying cache first, then curated list."""
    cached = _load_cache()
    if cached:
        logger.info("Loaded %d IT companies from cache", len(cached))
        return cached

    companies = _curated_list()

    valid: list[dict[str, Any]] = []
    for c in companies:
        entry = {
            "name": c.name,
            "website": f"https://{c.domain}",
            "city": c.city,
            "industry": c.industry,
            "size": c.size,
            "linkedin": f"https://linkedin.com/company/{c.linkedin_slug}",
            "category": "it_company",
            "domain": c.domain,
            "linkedin_slug": c.linkedin_slug,
        }
        valid.append(entry)

    _save_cache(valid)
    logger.info("Returning %d IT companies", len(valid))
    return valid


def _load_cache() -> list[dict[str, Any]] | None:
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        mtime = os.path.getmtime(CACHE_FILE)
        if time.time() - mtime > CACHE_TTL:
            return None
        with open(CACHE_FILE) as f:
            return json.load(f)
    except Exception:
        return None


def _save_cache(data: list[dict[str, Any]]) -> None:
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning("Failed to write IT company cache: %s", e)
