"""AI Platform — provider-agnostic, prompt-driven, versioned.

Core components:
- AIService: main orchestration layer
- Platform: provider abstraction (OpenRouter, local, future)
- Prompts: versioned prompt registry with variable interpolation
- Utils: token counting, cost tracking, logging, retry, validation
"""

from backend.ai.client import OpenRouterClient
from backend.ai.cover_letter import CoverLetterGenerator
from backend.ai.matching import JobMatcher
from backend.ai.platform import (
    AIProvider,
    AIRequest,
    AIResponse,
    ModelInfo,
    ModelRegistry,
    OpenRouterProvider,
)
from backend.ai.prompts import Prompt, PromptRegistry, PromptVersion, get_prompt_registry
from backend.ai.resume import ResumeParser
from backend.ai.services import AIService
from backend.ai.skill_gap import SkillGapAnalyser

__all__ = [
    "AIProvider",
    "AIRequest",
    "AIResponse",
    "AIService",
    "CoverLetterGenerator",
    "JobMatcher",
    "ModelInfo",
    "ModelRegistry",
    "OpenRouterClient",
    "OpenRouterProvider",
    "Prompt",
    "PromptRegistry",
    "PromptVersion",
    "ResumeParser",
    "SkillGapAnalyser",
    "get_prompt_registry",
]
