"""Retry and fallback logic for AI requests."""

import asyncio
import logging

from backend.ai.platform.provider import AIProvider, AIRequest, AIResponse
from backend.ai.platform.registry import ModelRegistry

logger = logging.getLogger("job_hunting.ai.retry")

_registry = ModelRegistry()


async def complete_with_retry(
    provider: AIProvider,
    request: AIRequest,
    *,
    max_retries: int = 2,
    fallback_model: str | None = None,
    backoff_base: float = 1.0,
) -> AIResponse:
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            return await provider.complete(request)
        except Exception as exc:
            last_error = exc
            logger.warning("AI request attempt %d/%d failed: %s", attempt + 1, max_retries, exc)
            if attempt < max_retries - 1:
                await asyncio.sleep(backoff_base * (2**attempt))

    if fallback_model and fallback_model != request.model:
        logger.info("Falling back to model %s", fallback_model)
        fb_request = AIRequest(
            messages=request.messages,
            model=fallback_model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            response_format=request.response_format,
            metadata=request.metadata,
        )
        try:
            return await provider.complete(fb_request)
        except Exception as exc:
            raise exc from last_error

    raise last_error or RuntimeError("AI request failed")
