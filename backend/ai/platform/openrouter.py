import logging
import time
from typing import Any

import httpx

from backend.ai.platform.provider import AIProvider, AIRequest, AIResponse, ModelInfo
from backend.ai.platform.registry import MODELS
from backend.config.settings import get_settings

logger = logging.getLogger("job_hunting.ai.openrouter")


class OpenRouterProvider(AIProvider):
    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.OPENROUTER_API_KEY
        self._base_url = settings.OPENROUTER_BASE_URL.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "Job Hunting AI",
                },
                timeout=httpx.Timeout(60.0),
            )
        return self._client

    async def complete(self, request: AIRequest) -> AIResponse:
        start = time.perf_counter()
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.response_format:
            payload["response_format"] = request.response_format

        client = await self._get_client()
        try:
            resp = await client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
            choices: list[dict[str, Any]] = data.get("choices", [])
            usage_raw: dict[str, Any] = data.get("usage", {})

            content = ""
            finish = "stop"
            if choices:
                msg: dict[str, str] = choices[0].get("message", {})
                content = msg.get("content", "")
                finish = choices[0].get("finish_reason", "stop")

            usage: dict[str, int] = {
                "input_tokens": int(usage_raw.get("prompt_tokens", 0)),
                "output_tokens": int(usage_raw.get("completion_tokens", 0)),
                "total_tokens": int(usage_raw.get("total_tokens", 0)),
            }

            return AIResponse(
                content=content,
                model=data.get("model", request.model),
                usage=usage,
                finish_reason=finish,
                provider="openrouter",
                latency_ms=(time.perf_counter() - start) * 1000,
            )
        except httpx.HTTPError as exc:
            logger.error("OpenRouter request failed: %s", exc)
            raise

    async def health(self) -> bool:
        try:
            client = await self._get_client()
            resp = await client.get("/models")
            return resp.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[ModelInfo]:
        return [m for m in MODELS.values() if m.provider == "openrouter"]

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
