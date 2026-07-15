"""OpenRouter API client wrapper.

Provides a minimal async HTTP client for calling LLM models via the
OpenRouter API.  Designed to be injected into AI services so that the
model, temperature, and other parameters are configurable per call.
"""

import logging
from typing import Any

import httpx

from backend.config.settings import get_settings

logger = logging.getLogger("job_hunting.ai.client")


class ClientError(Exception):
    pass


class OpenRouterClient:
    """Async client for OpenRouter's chat-completions API."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client = httpx.AsyncClient(
            base_url=self._settings.OPENROUTER_BASE_URL,
            headers={
                "Authorization": f"Bearer {self._settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": self._settings.APP_NAME,
            },
            timeout=60.0,
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Send a chat completion request and return the response text."""
        payload: dict[str, Any] = {
            "model": model or self._settings.OPENROUTER_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            resp = await self._client.post(
                "/chat/completions",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            choices: list[dict[str, Any]] = data.get("choices", [])
            if choices:
                msg: dict[str, str] = choices[0].get("message", {})
                return msg.get("content", "")
            return ""
        except httpx.HTTPError as exc:
            logger.error("OpenRouter request failed: %s", exc)
            raise ClientError(f"OpenRouter request failed: {exc}") from exc

    async def close(self) -> None:
        await self._client.aclose()
