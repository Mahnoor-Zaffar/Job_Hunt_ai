"""Email address validation for startup HR contacts.

Tiers:
  1. MX record check — does the domain accept mail at all?
  2. Website scraping — find real emails on contact/careers pages
  3. SMTP handshake (optional) — verify mailbox exists
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger("job_hunting.email_validator")

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

CONTACT_PATHS = ["/contact", "/careers", "/team"]


@dataclass
class EmailValidation:
    email: str
    confidence: int  # 0–100
    label: str  # verified | confirmed | live | probable | invalid
    source: str = "guess"
    detail: str = ""


async def check_mx(domain: str) -> bool:
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, "MX", lifetime=5)
        return len(answers) > 0
    except Exception:
        return False


async def scrape_website_emails(domain: str, timeout: float = 5.0) -> list[str]:
    found: set[str] = set()
    base_url = f"https://{domain}"
    paths = ["", *CONTACT_PATHS]
    seen_urls: set[str] = set()
    per_page = 3.0
    async with httpx.AsyncClient(timeout=httpx.Timeout(per_page, connect=2.0), follow_redirects=True, verify=False) as client:
        for path in paths:
            url = f"{base_url}{path}"
            if url in seen_urls:
                continue
            seen_urls.add(url)
            try:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})
                if resp.status_code != 200:
                    continue
                text = resp.text
                for match in EMAIL_PATTERN.findall(text):
                    local, mail_domain = match.split("@", 1)
                    mail_domain = mail_domain.lower()
                    skip_domains = {"example.com", "domain.com", "yourdomain.com", "email.com"}
                    if mail_domain in skip_domains:
                        continue
                    if any(skip in mail_domain for skip in [".png", ".jpg", ".gif", ".svg", ".css", ".js"]):
                        continue
                    found.add(match.lower())
            except Exception:
                continue
    return list(found)


async def validate_emails_for_domain(
    domain: str,
    guessed_emails: list[dict[str, Any]],
    perform_smtp: bool = False,
) -> list[dict[str, Any]]:
    has_mx = await check_mx(domain)

    scraped = await scrape_website_emails(domain)
    scraped_set = set(scraped)

    validated: list[dict[str, Any]] = []
    for entry in guessed_emails:
        email = entry["email"]
        local_part = email.split("@")[0]

        if email in scraped_set:
            confidence = 100
            label = "verified"
            source = "website"
            detail = "Found on company website"
        elif any(email.lower() == s.lower() for s in scraped):
            confidence = 90
            label = "verified"
            source = "website"
            detail = "Found on company website (case normalized)"
        elif any(local_part in s.lower() for s in scraped):
            confidence = 80
            label = "confirmed"
            source = "website"
            detail = "Similar email found on website"
        elif not has_mx:
            confidence = 0
            label = "invalid"
            source = "mx"
            detail = "Domain has no mail servers"
        elif perform_smtp:
            exists = await smtp_verify(email)
            if exists:
                confidence = 70
                label = "live"
                source = "smtp"
                detail = "Mailbox confirmed via SMTP"
            else:
                confidence = 30
                label = "probable"
                source = "smtp"
                detail = "SMTP check failed, may still be valid"
        else:
            confidence = 50
            label = "probable"
            source = "mx"
            detail = "Domain accepts mail"

        validated.append({
            "email": email,
            "priority": entry["priority"],
            "label": entry["label"],
            "confidence": confidence,
            "confidence_label": label,
            "detail": detail,
            "source": source,
        })

    # Add any verified emails from website that weren't in our guesses
    for se in scraped:
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
        mx_records = await _resolve_mx(domain)
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


async def _resolve_mx(domain: str) -> list[str]:
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, "MX", lifetime=5)
        return [str(r.exchange).rstrip(".") for r in answers]
    except Exception:
        return []
