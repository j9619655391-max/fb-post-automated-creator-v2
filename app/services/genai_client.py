from dataclasses import dataclass
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import requests

from app.core.config import settings


@dataclass(frozen=True)
class GenerationUsage:
    prompt_tokens: int = 0
    candidates_tokens: int = 0
    thoughts_tokens: int = 0
    cached_content_tokens: int = 0
    total_tokens: int = 0


class OpenRouterProviderError(ValueError):
    """Raised when OpenRouter rejects or cannot complete a generation request."""


@dataclass
class OpenRouterResponse:
    text: str
    usage_metadata: Any
    model: str


class _OpenRouterModels:
    def generate_content(self, *, model: str, contents: str) -> OpenRouterResponse:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": contents}],
            "temperature": 0.7,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }
        if settings.openrouter_http_referer:
            headers["HTTP-Referer"] = settings.openrouter_http_referer
        if settings.openrouter_app_title:
            headers["X-OpenRouter-Title"] = settings.openrouter_app_title

        try:
            response = requests.post(
                f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
                timeout=settings.openrouter_timeout_seconds,
            )
        except requests.RequestException as exc:
            raise OpenRouterProviderError("OpenRouter request failed due to a network error") from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise OpenRouterProviderError(
                f"OpenRouter returned an invalid response ({response.status_code})"
            ) from exc

        if response.status_code >= 400:
            error = data.get("error") if isinstance(data, dict) else None
            message = error.get("message") if isinstance(error, dict) else None
            raise OpenRouterProviderError(
                f"OpenRouter request failed ({response.status_code}): {message or 'provider error'}"
            )

        choices = data.get("choices") if isinstance(data, dict) else None
        if not choices or not isinstance(choices[0], dict):
            raise OpenRouterProviderError("OpenRouter returned no completion choices")
        message = choices[0].get("message") or {}
        content = message.get("content") if isinstance(message, dict) else ""
        if isinstance(content, list):
            content = "".join(
                str(part.get("text") or "") if isinstance(part, dict) else str(part)
                for part in content
            )
        if not isinstance(content, str) or not content.strip():
            raise OpenRouterProviderError("OpenRouter returned an empty completion")

        usage = data.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or prompt_tokens + completion_tokens)
        metadata = SimpleNamespace(
            prompt_tokens=prompt_tokens,
            prompt_token_count=prompt_tokens,
            candidates_tokens=completion_tokens,
            candidates_token_count=completion_tokens,
            thoughts_tokens=0,
            thoughts_token_count=0,
            cached_content_tokens=0,
            cached_content_token_count=0,
            total_tokens=total_tokens,
            total_token_count=total_tokens,
        )
        return OpenRouterResponse(
            text=content,
            usage_metadata=metadata,
            model=str(data.get("model") or model),
        )


class OpenRouterClient:
    def __init__(self) -> None:
        self.models = _OpenRouterModels()

    def close(self) -> None:
        return None


def active_provider_and_model() -> tuple[str, str]:
    provider = (settings.ai_provider or "gemini").strip().lower()
    if provider == "gemini":
        return provider, settings.gemini_model
    if provider == "openrouter":
        return provider, settings.openrouter_model
    raise ValueError(f"Unsupported AI provider: {provider}")


def get_client(provider: str | None = None):
    """Create the configured AI provider client without exposing provider secrets."""
    selected_provider, _model = active_provider_and_model() if provider is None else ((provider.strip().lower()), "")
    provider = selected_provider
    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured")
        from google import genai

        return genai.Client(api_key=settings.gemini_api_key)
    if provider == "openrouter":
        if not settings.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured")
        return OpenRouterClient()
    raise ValueError(f"Unsupported AI provider: {provider}")


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

    prompt = value("prompt_token_count", "promptTokenCount", "prompt_tokens")
    candidates = value("candidates_token_count", "candidatesTokenCount", "completion_tokens")
    thoughts = value("thoughts_token_count", "thoughtsTokenCount")
    cached = value("cached_content_token_count", "cachedContentTokenCount")
    total = value("total_token_count", "totalTokenCount", "total_tokens") or prompt + candidates + thoughts
    return GenerationUsage(prompt, candidates, thoughts, cached, total)


def cost_rates(provider: str | None = None) -> tuple[float, float]:
    selected = (provider or "gemini").strip().lower()
    if selected == "openrouter":
        return settings.openrouter_input_cost_per_million_usd, settings.openrouter_output_cost_per_million_usd
    return settings.gemini_input_cost_per_million_usd, settings.gemini_output_cost_per_million_usd


def calculate_cost(usage: GenerationUsage, provider: str | None = None) -> Decimal:
    """Calculate estimated USD cost from provider-configured token rates."""
    input_rate, output_rate = cost_rates(provider)
    input_tokens = usage.prompt_tokens + usage.cached_content_tokens
    output_tokens = usage.candidates_tokens + usage.thoughts_tokens
    input_cost = Decimal(str(input_rate)) * Decimal(input_tokens) / Decimal(1_000_000)
    output_cost = Decimal(str(output_rate)) * Decimal(output_tokens) / Decimal(1_000_000)
    return (input_cost + output_cost).quantize(Decimal("0.00000001"))


def close_client(client: Any) -> None:
    close = getattr(client, "close", None)
    if callable(close):
        close()
