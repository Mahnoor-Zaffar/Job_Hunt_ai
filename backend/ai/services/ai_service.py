"""AI Service — main orchestration layer.

Ties together providers, prompts, models, retry logic, token tracking,
cost estimation, and structured logging into a single service interface.
"""

from typing import Any

from backend.ai.platform.openrouter import OpenRouterProvider
from backend.ai.platform.provider import AIProvider, AIRequest, AIResponse
from backend.ai.platform.registry import ModelRegistry
from backend.ai.prompts.defaults import get_prompt_registry
from backend.ai.prompts.registry import PromptRegistry
from backend.ai.utils.logging import AIRequestLogger
from backend.ai.utils.retry import complete_with_retry
from backend.ai.utils.tokens import estimate_request_tokens
from backend.ai.utils.validation import JSONValidationError, safe_extract_json


class AIService:
    def __init__(
        self,
        provider: AIProvider | None = None,
        models: ModelRegistry | None = None,
        prompts: PromptRegistry | None = None,
        request_logger: AIRequestLogger | None = None,
    ) -> None:
        self._provider = provider or OpenRouterProvider()
        self._models = models or ModelRegistry()
        self._prompts = prompts or get_prompt_registry()
        self._logger = request_logger or AIRequestLogger()

    async def generate(
        self,
        prompt_name: str,
        variables: dict[str, str] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        metadata: dict[str, str] | None = None,
        json_output: bool = False,
        required_keys: list[str] | None = None,
        fallback: str | None = None,
    ) -> dict[str, Any]:
        rendered = self._prompts.render(prompt_name, variables)

        model_id = model or self._models.get_default().id
        if fallback is None:
            fb_info = self._models.get_fallback(model_id)
            fallback = fb_info.id

        request = AIRequest(
            messages=[{"role": "user", "content": rendered}],
            model=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"} if json_output else None,
            metadata=metadata or {},
        )
        request.metadata["prompt"] = prompt_name

        input_tokens = estimate_request_tokens(request.messages)

        try:
            response = await complete_with_retry(self._provider, request, fallback_model=fallback)
            self._logger.log(request, response, success=True)
        except Exception as exc:
            fail_response = AIResponse(
                content="",
                model=model_id,
                provider="error",
                usage={"input_tokens": input_tokens, "output_tokens": 0},
            )
            self._logger.log(request, fail_response, success=False, error=str(exc))
            raise

        if json_output:
            try:
                extracted = safe_extract_json(response.content)
                if required_keys:
                    from backend.ai.utils.validation import validate_schema

                    return validate_schema(extracted, required_keys)
                return extracted
            except JSONValidationError:
                return {"raw_response": response.content}

        return {"content": response.content}

    async def generate_text(
        self,
        prompt_name: str,
        variables: dict[str, str] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        result = await self.generate(
            prompt_name, variables, model=model, temperature=temperature, max_tokens=max_tokens
        )
        return str(result.get("content", ""))

    async def generate_json(
        self,
        prompt_name: str,
        variables: dict[str, str] | None = None,
        *,
        model: str | None = None,
        required_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        return await self.generate(
            prompt_name,
            variables,
            model=model,
            temperature=0.2,
            json_output=True,
            required_keys=required_keys,
        )

    def get_stats(self) -> dict[str, Any]:
        return self._logger.get_stats()

    def get_prompts(self) -> list[str]:
        return self._prompts.list_names()

    def get_models(self) -> list[dict[str, Any]]:
        models = self._models.list_active()
        return [
            {
                "id": m.id,
                "name": m.name,
                "provider": m.provider,
                "max_tokens": m.max_tokens,
                "cost_input": m.cost_per_1k_input,
                "cost_output": m.cost_per_1k_output,
                "tags": m.tags,
            }
            for m in models
        ]

    async def close(self) -> None:
        close_fn = getattr(self._provider, "close", None)
        if close_fn is not None:
            await close_fn()
