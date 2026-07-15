"""Telegram notification service.

Sends job alerts and notifications via the Telegram Bot API using
async HTTP requests.  Falls back gracefully when the bot token is
not configured.
"""

import logging
from typing import Any

import httpx

from backend.config.settings import get_settings

logger = logging.getLogger("job_hunting.notifications.telegram")

TELEGRAM_API = "https://api.telegram.org"


class TelegramNotifier:
    """Async Telegram notification sender."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._token = self._settings.TELEGRAM_BOT_TOKEN
        self._chat_id = self._settings.TELEGRAM_CHAT_ID
        self._client: httpx.AsyncClient | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self._token and self._chat_id)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15.0)
        return self._client

    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        if not self.is_configured:
            logger.debug("Telegram not configured — skipping message")
            return False
        try:
            client = await self._get_client()
            resp = await client.post(
                f"{TELEGRAM_API}/bot{self._token}/sendMessage",
                json={
                    "chat_id": self._chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True,
                },
            )
            resp.raise_for_status()
            return True
        except Exception:
            logger.exception("Failed to send Telegram message")
            return False

    async def send_job_alert(
        self,
        title: str,
        company: str,
        location: str,
        url: str,
        *,
        salary: str | None = None,
        match_score: float | None = None,
        skills: list[str] | None = None,
    ) -> bool:
        """Format and send a job alert message."""
        lines = [f"<b>{title}</b>", f"<i>{company}</i> — {location}"]
        if salary:
            lines.append(f"💰 {salary}")
        if skills:
            lines.append(f"🛠️ {', '.join(skills[:8])}")
        if match_score is not None:
            lines.append(f"🎯 Match: {match_score:.0%}")
        lines.append(f"\n🔗 {url}")

        return await self.send_message("\n".join(lines))

    async def send_batch(self, alerts: list[dict[str, Any]], limit: int = 5) -> int:
        sent = 0
        for alert in alerts[:limit]:
            success = await self.send_job_alert(
                title=str(alert.get("title", "")),
                company=str(alert.get("company", "")),
                location=str(alert.get("location", "")),
                url=str(alert.get("url", "")),
                salary=alert.get("salary"),
                match_score=alert.get("match_score"),
                skills=alert.get("skills"),
            )
            if success:
                sent += 1
        return sent

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
