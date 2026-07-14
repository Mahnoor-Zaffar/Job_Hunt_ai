from typing import Any

import httpx

from backend.scrapers.exceptions import (
    FetchError,
    ParseError,
    RateLimitError,
    ScraperTimeoutError,
)

_RATE_LIMIT_DELAY = 0.5


class HttpClient:
    """Reusable async HTTP client with retry, rate limiting, and connection pooling.

    Designed to be shared across scrapers to avoid connection churn.
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._timeout = timeout
        self._max_retries = max_retries
        self._base_headers = headers or {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                headers=self._base_headers,
            )
        return self._client

    async def get(self, url: str, **kwargs: Any) -> str:
        client = await self._get_client()
        last_exc: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                resp = await client.get(url, **kwargs)
                if resp.status_code == 429:
                    raise RateLimitError(f"Rate limited on {url}", source="httpx")
                resp.raise_for_status()
                return resp.text
            except RateLimitError:
                raise
            except httpx.TimeoutException:
                last_exc = ScraperTimeoutError(
                    f"Timeout on {url} (attempt {attempt + 1})",
                    source="httpx",
                )
            except httpx.HTTPStatusError as exc:
                last_exc = FetchError(
                    f"HTTP {exc.response.status_code} on {url}",
                    source="httpx",
                )
            except httpx.RequestError as exc:
                last_exc = FetchError(f"Request failed on {url}: {exc}", source="httpx")

        raise FetchError(
            f"Max retries ({self._max_retries}) exhausted on {url}",
            source="httpx",
        ) from last_exc

    async def get_json(self, url: str, **kwargs: Any) -> Any:
        text = await self.get(url, **kwargs)
        try:
            import json as json_mod

            return json_mod.loads(text)
        except ValueError as exc:
            raise ParseError(f"Invalid JSON from {url}: {exc}", source="httpx") from exc

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
