"""AI request logger — structured logging for every AI call."""

import logging
from typing import Any

from backend.ai.platform.provider import AIRequest, AIResponse
from backend.ai.utils.tokens import format_tokens

logger = logging.getLogger("job_hunting.ai.logger")


class AIRequestLogger:
    def __init__(self) -> None:
        self._history: list[dict[str, Any]] = []

    def log(
        self,
        request: AIRequest,
        response: AIResponse,
        *,
        success: bool = True,
        error: str | None = None,
    ) -> None:
        entry: dict[str, Any] = {
            "model": response.model,
            "provider": response.provider,
            "success": success,
            "input_tokens": response.usage.get("input_tokens", 0),
            "output_tokens": response.usage.get("output_tokens", 0),
            "latency_ms": round(response.latency_ms, 1),
            "finish_reason": response.finish_reason,
            "metadata": request.metadata,
        }
        if error:
            entry["error"] = error

        self._history.append(entry)

        status = "OK" if success else "FAIL"
        logger.info(
            "ai_request model=%s provider=%s status=%s in=%s out=%s latency=%.0fms",
            response.model,
            response.provider,
            status,
            format_tokens(entry["input_tokens"]),
            format_tokens(entry["output_tokens"]),
            response.latency_ms,
        )

    def get_history(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._history[-limit:]

    def get_stats(self) -> dict[str, Any]:
        if not self._history:
            return {}
        total_calls = len(self._history)
        succeeded = sum(1 for e in self._history if e["success"])
        total_in = sum(e["input_tokens"] for e in self._history)
        total_out = sum(e["output_tokens"] for e in self._history)
        avg_latency = sum(e["latency_ms"] for e in self._history) / total_calls
        return {
            "total_calls": total_calls,
            "succeeded": succeeded,
            "failed": total_calls - succeeded,
            "total_input_tokens": total_in,
            "total_output_tokens": total_out,
            "avg_latency_ms": round(avg_latency, 1),
        }
