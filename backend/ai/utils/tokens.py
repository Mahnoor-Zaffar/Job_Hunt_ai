"""Token counting — approximate counts using character-based heuristics.

When tiktoken is installed, uses it for accurate counts.
Falls back to character/4 estimation otherwise.
"""

import logging

logger = logging.getLogger("job_hunting.ai.tokens")

try:
    import tiktoken

    _enc = tiktoken.get_encoding("cl100k_base")

    def count_tokens(text: str) -> int:
        return len(_enc.encode(text))

except ImportError:

    def count_tokens(text: str) -> int:
        return len(text) // 4


def estimate_request_tokens(messages: list[dict[str, str]]) -> int:
    total = 0
    for msg in messages:
        total += count_tokens(msg.get("content", ""))
        total += 4
    return total + 2


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    cost_per_1k_input: float,
    cost_per_1k_output: float,
) -> float:
    return cost_per_1k_input * input_tokens / 1000 + cost_per_1k_output * output_tokens / 1000


def format_tokens(count: int) -> str:
    if count >= 1000:
        return f"{count / 1000:.1f}k"
    return str(count)
