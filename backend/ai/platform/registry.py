"""Model registry — definitions for all supported models."""

from backend.ai.platform.provider import ModelInfo

MODELS: dict[str, ModelInfo] = {
    # OpenRouter models (current as of 2026)
    "anthropic/claude-sonnet-5": ModelInfo(
        id="anthropic/claude-sonnet-5",
        name="Claude Sonnet 5",
        provider="openrouter",
        max_tokens=200000,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        supports_json=True,
        tags=["reasoning", "general", "primary"],
    ),
    "openai/gpt-5.6-terra": ModelInfo(
        id="openai/gpt-5.6-terra",
        name="GPT 5.6 Terra",
        provider="openrouter",
        max_tokens=128000,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        supports_json=True,
        supports_vision=True,
        tags=["reasoning", "multimodal", "primary"],
    ),
    "openai/gpt-5.6-sol": ModelInfo(
        id="openai/gpt-5.6-sol",
        name="GPT 5.6 Sol",
        provider="openrouter",
        max_tokens=128000,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        supports_json=True,
        supports_vision=True,
        tags=["fast", "cheap", "general"],
    ),
    "google/gemini-3.6-flash": ModelInfo(
        id="google/gemini-3.6-flash",
        name="Gemini 3.6 Flash",
        provider="openrouter",
        max_tokens=1048576,
        cost_per_1k_input=0.0001,
        cost_per_1k_output=0.0004,
        supports_json=True,
        tags=["fast", "cheap", "large_context"],
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
        is_deprecated=True,
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
        return MODELS["openai/gpt-5.6-terra"]

    def get_fallback(self, primary_id: str) -> ModelInfo:
        for model in MODELS.values():
            if model.id != primary_id and not model.is_deprecated and "general" in model.tags:
                return model
        return MODELS["openai/gpt-5.6-sol"]

    def estimate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        model = self.get(model_id)
        if model is None:
            return 0.0
        return (
            model.cost_per_1k_input * input_tokens / 1000
            + model.cost_per_1k_output * output_tokens / 1000
        )
