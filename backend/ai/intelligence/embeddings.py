"""Local embedding service using sentence-transformers.

Produces dense vector embeddings for resumes, jobs, and technologies.
Falls back to a zero-vector stub when sentence-transformers is not
installed (e.g., in CI or minimal deployments).

Embeddings can be stored in PostgreSQL (pgvector) for future
semantic search without schema changes.
"""

import logging
from typing import Any

logger = logging.getLogger("job_hunting.intelligence.embeddings")

try:
    from sentence_transformers import SentenceTransformer

    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model_name = model_name
        self._model: Any = None
        if _AVAILABLE:
            try:
                self._model = SentenceTransformer(model_name)
                logger.info("Loaded embedding model: %s", model_name)
            except Exception:
                logger.warning("Failed to load embedding model — using stub")
                self._model = None

    def embed(self, text: str) -> list[float]:
        if self._model is not None:
            result = self._model.encode([text], show_progress_bar=False)
            return list(result[0])

        return self._fallback_embed(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self._model is not None:
            results = self._model.encode(texts, show_progress_bar=False)
            return [list(r) for r in results]

        return [self._fallback_embed(t) for t in texts]

    def similarity(self, a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    def embed_job(
        self, title: str, company: str, description: str | None, skills: list[str] | None
    ) -> list[float]:
        text = f"{title} at {company}. "
        if description:
            text += description[:2000] + " "
        if skills:
            text += "Skills: " + ", ".join(skills)
        return self.embed(text)

    def embed_resume(
        self, parsed_text: str, skills: list[str] | None, name: str = ""
    ) -> list[float]:
        text = f"{name}. {parsed_text[:2000]}"
        if skills:
            text += " Skills: " + ", ".join(skills)
        return self.embed(text)

    def embed_technology(self, tech_name: str) -> list[float]:
        return self.embed(f"Technology: {tech_name}")

    @property
    def is_available(self) -> bool:
        return self._model is not None

    @staticmethod
    def _fallback_embed(text: str) -> list[float]:
        h = hash(text) % 100000
        result = [(h * (i + 1) % 1000) / 1000.0 for i in range(384)]
        norm = sum(x * x for x in result) ** 0.5
        return [x / norm for x in result] if norm > 0 else result
