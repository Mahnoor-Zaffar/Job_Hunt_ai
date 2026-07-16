"""JSON output validation for LLM responses.

Validates that LLM responses conform to expected schemas.
Extracts JSON from markdown-wrapped or raw responses.
"""

import json as json_mod
import logging
import re
from typing import Any

logger = logging.getLogger("job_hunting.ai.validation")


class JSONValidationError(Exception):
    pass


def extract_json(text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            result = json_mod.loads(match.group(0))
            return result  # type: ignore[no-any-return]
        except json_mod.JSONDecodeError as exc:
            raise JSONValidationError(f"Invalid JSON: {exc}") from exc

    match_arr = re.search(r"\[.*\]", text, re.DOTALL)
    if match_arr:
        try:
            result = json_mod.loads(match_arr.group(0))
            return {"items": result}
        except json_mod.JSONDecodeError as exc:
            raise JSONValidationError(f"Invalid JSON array: {exc}") from exc

    raise JSONValidationError("No JSON object or array found in response")


def validate_schema(data: dict[str, Any], required_keys: list[str]) -> dict[str, Any]:
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise JSONValidationError(f"Missing required keys: {missing}")
    return data


def safe_extract_json(text: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        return extract_json(text)
    except JSONValidationError:
        logger.warning("Failed to extract JSON from response")
        return default or {"raw_response": text}
