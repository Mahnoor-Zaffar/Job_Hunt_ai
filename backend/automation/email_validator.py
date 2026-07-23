"""Email address validation for startup HR contacts.

Tiers:
  1. MX record check — does the domain accept mail at all?
  2. Website scraping — find real emails on contact/careers/blog/team pages
  3. Catch-all detection — test domain with random address
  4. SMTP handshake — verify mailbox exists via RCPT TO
  5. Email permutation from names found on team pages
"""

import asyncio
import logging
import re
import random
import string
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger("job_hunting.email_validator")

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

SCRAPE_PATHS = [
    "", "/about", "/about-us", "/contact", "/contact-us",
    "/careers", "/career", "/team", "/people", "/founders",
    "/leadership", "/management", "/company", "/blog",
]

FOLLOW_LINK_PATTERNS = re.compile(
    r"/(team|people|founders?|leadership|about|profile|member|author)/\S+",
    re.I,
)

NAME_ON_PAGE_PATTERN = re.compile(
    r'(?:<h[12][^>]*>|class=["\'](?:name|title|member-name)[^>]*>|alt=["\'])\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
)

DOMAIN_SKIP_PATTERNS = re.compile(r"\.(png|jpg|gif|svg|css|js|ico|woff|ttf)$", re.I)
SKIP_DOMAINS = {"example.com", "domain.com", "yourdomain.com", "email.com", "test.com", "mail.com"}


@dataclass
class EmailValidation:
    email: str
    confidence: int
    label: str
    source: str = "guess"
    detail: str = ""


async def check_mx(domain: str) -> bool:
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, "MX", lifetime=5)
        return len(answers) > 0
    except Exception:
        return False


async def resolve_mx(domain: str) -> list[str]:
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, "MX", lifetime=5)
        return [str(r.exchange).rstrip(".") for r in answers]
    except Exception:
        return []


async def is_catch_all(domain: str) -> bool:
    import dns.resolver
    rand = "".join(random.choices(string.ascii_lowercase, k=12))
    test_email = f"{rand}@{domain}"
    mx_hosts = await resolve_mx(domain)
    if not mx_hosts:
        return False
    try:
        import aiosmtplib
        smtp = aiosmtplib.SMTP(hostname=mx_hosts[0], port=25, timeout=5)
        await smtp.connect()
        await smtp.ehlo()
        await smtp.mail("verify@example.com")
        code, _ = await smtp.rcpt(test_email)
        await smtp.quit()
        return code == 250
    except Exception:
        return False


def extract_names_from_html(html: str) -> list[str]:
    names: set[str] = set()
    for match in NAME_ON_PAGE_PATTERN.finditer(html):
        name = match.group(1).strip()
        if len(name.split()) >= 2:
            names.add(name)
    return list(names)


def generate_email_permutations(name: str, domain: str) -> list[str]:
    parts = name.lower().split()
    if len(parts) < 2:
        return []
    first, last = parts[0], parts[-1]
    patterns = [
        f"{first}@{domain}",
        f"{first}.{last}@{domain}",
        f"{first}{last}@{domain}",
        f"{first[0]}{last}@{domain}",
        f"{first[0]}.{last}@{domain}",
        f"{first}_{last}@{domain}",
        f"{first}-{last}@{domain}",
        f"{last}.{first}@{domain}",
        f"{last}@{domain}",
    ]
    if len(parts) > 2:
        patterns.append(f"{first}.{parts[1]}@{domain}")
        patterns.append(f"{first[0]}{parts[1][0]}{last}@{domain}")
    return patterns


async def fetch_page(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        resp = await client.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
            follow_redirects=True,
        )
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return None


def extract_emails_from_html(html: str) -> set[str]:
    found: set[str] = set()
    for match in EMAIL_PATTERN.findall(html):
        local, mail_domain = match.split("@", 1)
        mail_domain = mail_domain.lower()
        if mail_domain in SKIP_DOMAINS:
            continue
        if DOMAIN_SKIP_PATTERNS.search(mail_domain):
            continue
        found.add(match.lower())
    return found


async def scrape_website_deep(domain: str, per_page: float = 3.0) -> dict[str, Any]:
    base_url = f"https://{domain}"
    found_emails: set[str] = set()
    found_names: list[str] = []
    visited: set[str] = set()

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(per_page, connect=2.0),
        follow_redirects=True,
        verify=False,
    ) as client:
        pages_to_visit = set()
        for path in SCRAPE_PATHS:
            pages_to_visit.add(f"{base_url}{path}")

        try:
            sitemap_text = await fetch_page(client, f"{base_url}/sitemap.xml")
            if sitemap_text:
                for url_match in re.finditer(r"<loc>(.*?)</loc>", sitemap_text):
                    u = url_match.group(1).strip()
                    if domain in u:
                        pages_to_visit.add(u)
        except Exception:
            pass

        follow_queue: list[str] = []
        for url in pages_to_visit:
            if url in visited:
                continue
            visited.add(url)
            html = await fetch_page(client, url)
            if html is None:
                continue

            for email in extract_emails_from_html(html):
                found_emails.add(email)

            names = extract_names_from_html(html)
            found_names.extend(names)

            for link_match in re.finditer(r'href=["\'](/[^"\']+)["\']', html):
                link = link_match.group(1)
                if FOLLOW_LINK_PATTERNS.search(link) and link not in visited:
                    full = urljoin(base_url, link)
                    if domain in full:
                        follow_queue.append(full)

        for url in follow_queue[:15]:
            if url in visited:
                continue
            visited.add(url)
            html = await fetch_page(client, url)
            if html is None:
                continue
            for email in extract_emails_from_html(html):
                found_emails.add(email)
            names = extract_names_from_html(html)
            found_names.extend(names)

    return {"emails": list(found_emails), "names": found_names}


async def validate_emails_for_domain(
    domain: str,
    guessed_emails: list[dict[str, Any]],
    perform_smtp: bool = True,
) -> list[dict[str, Any]]:
    has_mx = await check_mx(domain)

    if not has_mx:
        return [
            {
                "email": e["email"],
                "priority": e["priority"],
                "label": e["label"],
                "confidence": 0,
                "confidence_label": "invalid",
                "detail": "Domain has no mail servers",
                "source": "mx",
            }
            for e in guessed_emails
        ]

    scrape_result = await scrape_website_deep(domain)
    scraped_emails = set(scrape_result["emails"])
    scraped_names = scrape_result["names"]

    is_catchall = False
    if perform_smtp:
        try:
            is_catchall = await asyncio.wait_for(is_catch_all(domain), timeout=8)
        except (TimeoutError, Exception):
            is_catchall = False

    validated: list[dict[str, Any]] = []

    for entry in guessed_emails:
        email = entry["email"]
        local_part = email.split("@")[0]

        if email in scraped_emails:
            confidence, label, source, detail = 100, "verified", "website", "Found on company website"
        elif any(email.lower() == s.lower() for s in scraped_emails):
            confidence, label, source, detail = 95, "verified", "website", "Found on company website (case normalized)"
        elif any(local_part in s.lower() for s in scraped_emails):
            confidence, label, source, detail = 80, "confirmed", "website", "Similar email found on website"
        elif any(
            local_part in name.lower().split()[0] or local_part in name.lower().split()[-1]
            for name in scraped_names
        ):
            confidence, label, source, detail = 70, "confirmed", "website", "Matches team member name"
        elif is_catchall:
            confidence, label, source, detail = 40, "probable", "catchall", "Domain uses catch-all, cannot verify individually"
        elif perform_smtp and not is_catchall:
            exists = await smtp_verify(email)
            if exists:
                confidence, label, source, detail = 75, "live", "smtp", "Mailbox confirmed via SMTP"
            else:
                confidence, label, source, detail = 25, "probable", "smtp", "SMTP check failed, may still be valid"
        else:
            confidence, label, source, detail = 50, "probable", "mx", "Domain accepts mail"

        validated.append({
            "email": email,
            "priority": entry["priority"],
            "label": entry["label"],
            "confidence": confidence,
            "confidence_label": label,
            "detail": detail,
            "source": source,
        })

    # Try email permutations from names found on site (capped, only plausible)
    existing_emails_lower = {v["email"].lower() for v in validated}
    guessed_local_parts = {e["email"].split("@")[0].lower() for e in guessed_emails}
    perm_count = 0
    for name in scraped_names:
        if perm_count >= 10:
            break
        perms = generate_email_permutations(name, domain)
        for perm in perms:
            if perm_count >= 10:
                break
            pl = perm.split("@")[0].lower()
            if any(g in pl for g in ["hr", "career", "job", "recruit", "talent", "people", "hello", "contact", "info"]):
                continue  # skip — these are already covered by guessed emails
            if perm.lower() in existing_emails_lower:
                continue
            if pl in guessed_local_parts:
                continue  # skip permutation if it matches our original guess for this domain
            validated.append({
                "email": perm,
                "priority": 3,
                "label": f"Permuted from {name}",
                "confidence": 65,
                "confidence_label": "probable",
                "detail": f"Generated from team member name: {name}",
                "source": "permutation",
            })
            existing_emails_lower.add(perm.lower())
            perm_count += 1

    # Add any verified emails from website not in our guesses
    for se in scraped_emails:
        if not any(se.lower() == v["email"].lower() for v in validated):
            validated.append({
                "email": se,
                "priority": 1,
                "label": "Found on website",
                "confidence": 100,
                "confidence_label": "verified",
                "detail": "Found on company website",
                "source": "website",
            })

    validated.sort(key=lambda x: (-x["confidence"], x["priority"]))
    return validated


async def smtp_verify(email: str, timeout: float = 5.0) -> bool:
    try:
        import aiosmtplib
        domain = email.split("@")[1]
        mx_records = await resolve_mx(domain)
        if not mx_records:
            return False
        mx_host = mx_records[0]
        smtp = aiosmtplib.SMTP(hostname=mx_host, port=25, timeout=timeout)
        await smtp.connect()
        await smtp.ehlo()
        code, _ = await smtp.mail("verify@example.com")
        if code != 250:
            await smtp.quit()
            return False
        code, _ = await smtp.rcpt(email)
        await smtp.quit()
        return code == 250
    except Exception:
        return False
