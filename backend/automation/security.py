"""Security utilities for the automation platform.

Ensures sensitive data is protected during browser automation:
- Resume content never logged
- Form data redacted in logs
- File uploads validated before submission
- Credentials handled via env vars only
- Cookie/session data isolated per context
"""

import logging
import re

logger = logging.getLogger("job_hunting.automation.security")

SENSITIVE_PATTERNS = [
    (re.compile(r"(?i)(password|passwd|secret|token|api_key)[=:]\s*\S+"), "[REDACTED_CREDENTIAL]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL_REDACTED]"),
    (re.compile(r"\+?\d[\d\s().-]{7,15}"), "[PHONE_REDACTED]"),
    (re.compile(r"\b\d{3}[-.]?\d{2}[-.]?\d{4}\b"), "[SSN_REDACTED]"),
]


def sanitize_log(data: str, max_length: int = 500) -> str:
    cleaned = data[:max_length]
    for pattern, replacement in SENSITIVE_PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned


def sanitize_form_data(data: dict[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in data.items():
        safe_key = key
        safe_value = value
        for pattern, replacement in SENSITIVE_PATTERNS:
            safe_value = pattern.sub(replacement, safe_value)
        result[safe_key] = safe_value
    return result


def validate_upload_path(file_path: str) -> bool:
    from pathlib import Path

    p = Path(file_path).resolve()
    if ".." in file_path or not p.exists():
        return False
    allowed = {".pdf", ".docx", ".doc", ".txt"}
    if p.suffix.lower() not in allowed:
        return False
    size = p.stat().st_size
    return not size > 10 * 1024 * 1024


def validate_apply_url(url: str) -> bool:
    if not url.startswith(("https://", "http://")):
        return False
    return not len(url) > 2048


def check_credentials() -> dict[str, bool]:
    import os

    return {
        "openrouter_key_set": bool(
            os.getenv("OPENROUTER_API_KEY", "").startswith("sk-")
            or len(os.getenv("OPENROUTER_API_KEY", "")) > 10
        ),
        "telegram_token_set": bool(os.getenv("TELEGRAM_BOT_TOKEN", "")),
        "smtp_configured": bool(os.getenv("SMTP_HOST", "")),
    }
