"""AI observability API — metrics, stats, evaluation, audit."""

from typing import Any

from fastapi import APIRouter
from pydantic import Field

from backend.ai.evaluation import run_evaluation
from backend.ai.platform.registry import ModelRegistry
from backend.ai.prompts.defaults import get_prompt_registry
from backend.ai.services.ai_service import AIService
from backend.schemas.base import BaseSchema

router = APIRouter(prefix="/ai", tags=["ai-observability"])


class AIStatsResponse(BaseSchema):
    total_calls: int = 0
    succeeded: int = 0
    failed: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    avg_latency_ms: float = 0.0


class ModelInfo(BaseSchema):
    id: str
    name: str
    provider: str
    max_tokens: int
    cost_input: float
    cost_output: float
    tags: list[str] = Field(default_factory=list)


class ModelsResponse(BaseSchema):
    models: list[ModelInfo] = Field(default_factory=list)
    total: int = 0


class PromptsResponse(BaseSchema):
    prompts: list[str] = Field(default_factory=list)
    total: int = 0


class EvaluationResponse(BaseSchema):
    prompts: dict[str, Any] = Field(default_factory=dict)
    models: dict[str, Any] = Field(default_factory=dict)
    resume: dict[str, Any] = Field(default_factory=dict)
    sanitizer: dict[str, Any] = Field(default_factory=dict)
    scoring: dict[str, Any] = Field(default_factory=dict)


class PromptDetailResponse(BaseSchema):
    name: str
    description: str = ""
    category: str = ""
    version: int = 1
    template_preview: str = ""
    variables: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    versions: int = 0


_ai_service = AIService()
_registry = ModelRegistry()


@router.get("/stats", response_model=AIStatsResponse)
async def ai_stats() -> AIStatsResponse:
    stats = _ai_service.get_stats()
    return AIStatsResponse(**stats)


@router.get("/models", response_model=ModelsResponse)
async def ai_models() -> ModelsResponse:
    models = _registry.list_active()
    return ModelsResponse(
        models=[
            ModelInfo(
                id=m.id,
                name=m.name,
                provider=m.provider,
                max_tokens=m.max_tokens,
                cost_input=m.cost_per_1k_input,
                cost_output=m.cost_per_1k_output,
                tags=m.tags,
            )
            for m in models
        ],
        total=len(models),
    )


@router.get("/prompts", response_model=PromptsResponse)
async def ai_prompts() -> PromptsResponse:
    pr = get_prompt_registry()
    names = pr.list_names()
    return PromptsResponse(prompts=names, total=len(names))


@router.get("/evaluate", response_model=EvaluationResponse)
async def ai_evaluate() -> EvaluationResponse:
    results = run_evaluation()
    return EvaluationResponse(**results)


@router.get("/prompts/{name}", response_model=PromptDetailResponse)
async def ai_prompt_detail(name: str) -> PromptDetailResponse:
    pr = get_prompt_registry()
    prompt = pr.get(name)
    if prompt is None:
        return PromptDetailResponse(name=name, description="not found")
    latest = prompt.latest
    return PromptDetailResponse(
        name=prompt.name,
        description=prompt.description,
        category=prompt.category,
        version=latest.version,
        template_preview=latest.template[:500],
        variables=latest.variables,
        tags=latest.tags,
        versions=len(prompt.versions),
    )
