from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.core.config import settings


@dataclass(frozen=True)
class GenerationUsage:
    prompt_tokens: int = 0
    candidates_tokens: int = 0
    thoughts_tokens: int = 0
    cached_content_tokens: int = 0
    total_tokens: int = 0


def get_client():
    """Create the supported Google GenAI client for the Gemini Developer API."""
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not configured")
    from google import genai

    return genai.Client(api_key=settings.gemini_api_key)


def extract_usage(response: Any) -> GenerationUsage:
    metadata = getattr(response, "usage_metadata", None)
    if not metadata:
        return GenerationUsage()

    def value(*names: str) -> int:
        for name in names:
            candidate = getattr(metadata, name, None)
            if candidate is not None:
                try:
                    return int(candidate)
                except (TypeError, ValueError):
                    return 0
        return 0

    prompt = value("prompt_token_count", "promptTokenCount")
    candidates = value("candidates_token_count", "candidatesTokenCount")
    thoughts = value("thoughts_token_count", "thoughtsTokenCount")
    cached = value("cached_content_token_count", "cachedContentTokenCount")
    total = value("total_token_count", "totalTokenCount") or prompt + candidates + thoughts
    return GenerationUsage(prompt, candidates, thoughts, cached, total)


def calculate_cost(usage: GenerationUsage) -> Decimal:
    """Calculate estimated USD cost from configured per-million-token rates."""
    input_tokens = usage.prompt_tokens + usage.cached_content_tokens
    output_tokens = usage.candidates_tokens + usage.thoughts_tokens
    input_cost = Decimal(str(settings.gemini_input_cost_per_million_usd)) * Decimal(input_tokens) / Decimal(1_000_000)
    output_cost = Decimal(str(settings.gemini_output_cost_per_million_usd)) * Decimal(output_tokens) / Decimal(1_000_000)
    return (input_cost + output_cost).quantize(Decimal("0.00000001"))


def close_client(client: Any) -> None:
    close = getattr(client, "close", None)
    if callable(close):
        close()
