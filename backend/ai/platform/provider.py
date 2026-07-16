"""AI provider abstraction — pluggable LLM backends.

Every provider implements the same async interface so the platform
can switch between OpenRouter, local models, or future providers
without changing application code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AIRequest:
    messages: list[dict[str, str]]
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    response_format: dict[str, str] | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class AIResponse:
    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"
    provider: str = ""
    latency_ms: float = 0.0


@dataclass
class ModelInfo:
    id: str
    name: str
    provider: str
    max_tokens: int = 4096
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    supports_json: bool = True
    supports_vision: bool = False
    supports_tools: bool = False
    is_deprecated: bool = False
    tags: list[str] = field(default_factory=list)


class AIProvider(ABC):
    @abstractmethod
    async def complete(self, request: AIRequest) -> AIResponse: ...

    @abstractmethod
    async def health(self) -> bool: ...

    @abstractmethod
    def list_models(self) -> list[ModelInfo]: ...
