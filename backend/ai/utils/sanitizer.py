"""Input sanitizer for AI prompts.

Prevents prompt injection, strips sensitive data, and truncates
user-generated content to safe lengths before inclusion in LLM calls.
"""

import re

MAX_CONTENT_LENGTH = 8000
MAX_SKILLS_LENGTH = 500

INJECTION_PATTERNS = [
    re.compile(r"(?i)ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?)"),
    re.compile(
        r"(?i)you\s+are\s+now\s+(a\s+)?(different|new|another)\s*(model|assistant|persona|role)"
    ),
    re.compile(r"(?i)system\s*prompt\s*[:=]"),
    re.compile(r"(?i)forget\s+(everything|all)\s+(you|before)"),
    re.compile(r"<\|.*?\|>"),
    re.compile(r"\{\{.*?\}\}"),
]


class InputSanitizer:
    def sanitize(self, content: str | None, max_length: int = MAX_CONTENT_LENGTH) -> str:
        if not content:
            return ""

        content = content.strip()

        for pattern in INJECTION_PATTERNS:
            if pattern.search(content):
                content = pattern.sub("[REDACTED]", content)

        content = content.replace("```", "")
        content = content.replace("system:", "SYSTEM COLON")

        if len(content) > max_length:
            content = content[:max_length] + "\n... [truncated]"

        return content

    def sanitize_for_prompt(self, variables: dict[str, str]) -> dict[str, str]:
        cleaned: dict[str, str] = {}
        for key, value in variables.items():
            if isinstance(value, str):
                cleaned[key] = self.sanitize(value)
            else:
                cleaned[key] = value
        return cleaned

    def sanitize_skills(self, skills: list[str] | None) -> list[str]:
        if not skills:
            return []
        return [
            re.sub(r"[^a-zA-Z0-9\s#+./]", "", s)[:50].strip()
            for s in skills[:20]
            if s and len(s) > 1
        ]

    def validate_filename(self, filename: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)[:255]
