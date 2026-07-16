"""Model registry — definitions for all supported models."""

from backend.ai.platform.provider import ModelInfo

MODELS: dict[str, ModelInfo] = {
    # OpenRouter models
    "anthropic/claude-3.5-sonnet": ModelInfo(
        id="anthropic/claude-3.5-sonnet",
        name="Claude 3.5 Sonnet",
        provider="openrouter",
        max_tokens=200000,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        supports_json=True,
        tags=["reasoning", "general", "primary"],
    ),
    "anthropic/claude-3-haiku": ModelInfo(
        id="anthropic/claude-3-haiku",
        name="Claude 3 Haiku",
        provider="openrouter",
        max_tokens=200000,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.00125,
        supports_json=True,
        tags=["fast", "cheap", "general"],
    ),
    "openai/gpt-4o": ModelInfo(
        id="openai/gpt-4o",
        name="GPT-4o",
        provider="openrouter",
        max_tokens=128000,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        supports_json=True,
        supports_vision=True,
        tags=["reasoning", "multimodal", "primary"],
    ),
    "openai/gpt-4o-mini": ModelInfo(
        id="openai/gpt-4o-mini",
        name="GPT-4o Mini",
        provider="openrouter",
        max_tokens=128000,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        supports_json=True,
        supports_vision=True,
        tags=["fast", "cheap", "general"],
    ),
    "google/gemini-2.0-flash": ModelInfo(
        id="google/gemini-2.0-flash",
        name="Gemini 2.0 Flash",
        provider="openrouter",
        max_tokens=1048576,
        cost_per_1k_input=0.0001,
        cost_per_1k_output=0.0004,
        supports_json=True,
        tags=["fast", "cheap", "large_context"],
    ),
    "meta-llama/llama-4-maverick": ModelInfo(
        id="meta-llama/llama-4-maverick",
        name="Llama 4 Maverick",
        provider="openrouter",
        max_tokens=131072,
        cost_per_1k_input=0.0002,
        cost_per_1k_output=0.0006,
        supports_json=True,
        tags=["open_source", "general"],
    ),
    "anthropic/claude-3-opus": ModelInfo(
        id="anthropic/claude-3-opus",
        name="Claude 3 Opus",
        provider="openrouter",
        max_tokens=200000,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        supports_json=True,
        tags=["reasoning", "premium"],
    ),
    "deepseek/deepseek-chat": ModelInfo(
        id="deepseek/deepseek-chat",
        name="DeepSeek Chat V3",
        provider="openrouter",
        max_tokens=65536,
        cost_per_1k_input=0.00014,
        cost_per_1k_output=0.00028,
        supports_json=True,
        tags=["cheap", "general"],
    ),
    # Local models (placeholder)
    "local/llama": ModelInfo(
        id="local/llama",
        name="Llama (Local)",
        provider="local",
        max_tokens=8192,
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        supports_json=False,
        tags=["local", "free"],
    ),
}


class ModelRegistry:
    def get(self, model_id: str) -> ModelInfo | None:
        return MODELS.get(model_id)

    def list_by_provider(self, provider: str) -> list[ModelInfo]:
        return [m for m in MODELS.values() if m.provider == provider]

    def list_by_tag(self, tag: str) -> list[ModelInfo]:
        return [m for m in MODELS.values() if tag in m.tags]

    def list_active(self) -> list[ModelInfo]:
        return [m for m in MODELS.values() if not m.is_deprecated]

    def get_default(self) -> ModelInfo:
        return MODELS["anthropic/claude-3.5-sonnet"]

    def get_fallback(self, primary_id: str) -> ModelInfo:
        for model in MODELS.values():
            if model.id != primary_id and not model.is_deprecated and "general" in model.tags:
                return model
        return MODELS["openai/gpt-4o-mini"]

    def estimate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        model = self.get(model_id)
        if model is None:
            return 0.0
        return (
            model.cost_per_1k_input * input_tokens / 1000
            + model.cost_per_1k_output * output_tokens / 1000
        )
