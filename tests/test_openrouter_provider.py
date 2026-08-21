from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.services import genai_client


def test_openrouter_response_normalizes_text_usage_and_resolved_model(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-openrouter-key")
    monkeypatch.setattr(settings, "openrouter_model", "openrouter/free")

    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "model": "nvidia/nemotron-nano-9b-v2:free",
                "choices": [{"message": {"content": "PROVIDER_OK"}}],
                "usage": {
                    "prompt_tokens": 21,
                    "completion_tokens": 8,
                    "total_tokens": 29,
                },
            }

    monkeypatch.setattr(genai_client.requests, "post", lambda *args, **kwargs: FakeResponse())
    response = genai_client.OpenRouterClient().models.generate_content(
        model="openrouter/free",
        contents="Reply with exactly PROVIDER_OK",
    )

    usage = genai_client.extract_usage(response)
    assert response.text == "PROVIDER_OK"
    assert response.model == "nvidia/nemotron-nano-9b-v2:free"
    assert usage.prompt_tokens == 21
    assert usage.candidates_tokens == 8
    assert usage.total_tokens == 29
    assert genai_client.calculate_cost(usage, provider="openrouter") == 0


def test_active_provider_selects_openrouter_model(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "openrouter")
    monkeypatch.setattr(settings, "openrouter_model", "meta-llama/llama-3.2-3b-instruct:free")
    assert genai_client.active_provider_and_model() == (
        "openrouter",
        "meta-llama/llama-3.2-3b-instruct:free",
    )


def test_openrouter_requires_server_side_key(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "openrouter")
    monkeypatch.setattr(settings, "openrouter_api_key", None)
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY is not configured"):
        genai_client.get_client()


def test_openrouter_maps_provider_error_without_leaking_key(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-openrouter-key")

    class FakeResponse:
        status_code = 429

        def json(self):
            return {"error": {"message": "rate limit exceeded"}}

    monkeypatch.setattr(genai_client.requests, "post", lambda *args, **kwargs: FakeResponse())
    with pytest.raises(genai_client.OpenRouterProviderError, match="429") as exc_info:
        genai_client.OpenRouterClient().models.generate_content(
            model="openrouter/free",
            contents="hello",
        )
    assert "test-openrouter-key" not in str(exc_info.value)


def test_provider_status_exposes_safe_metadata_only(client, api, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "openrouter")
    monkeypatch.setattr(settings, "openrouter_api_key", "test-openrouter-key")
    monkeypatch.setattr(settings, "openrouter_model", "openrouter/free")

    response = client.get(f"{api}/generation/provider", headers=auth_headers)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["provider"] == "openrouter"
    assert payload["model"] == "openrouter/free"
    assert payload["configured"] is True
    assert payload["free_model"] is True
    assert "api_key" not in payload
    assert "test-openrouter-key" not in response.text


def test_provider_health_reports_recent_failure_alert(db, monkeypatch):
    from datetime import datetime, timezone

    from app.models.content_generation import ContentGenerationJob, GenerationStatus
    from app.services.ai_provider_health_service import collect_ai_provider_health

    monkeypatch.setattr(settings, "ai_provider", "openrouter")
    monkeypatch.setattr(settings, "openrouter_api_key", "test-openrouter-key")
    monkeypatch.setattr(settings, "openrouter_model", "openrouter/free")
    monkeypatch.setattr(settings, "ai_failure_alert_threshold", 1)
    monkeypatch.setattr(settings, "ai_failure_alert_window_minutes", 60)

    job = ContentGenerationJob(
        requested_by_id=1,
        category_name="Operations",
        model="openrouter/free",
        provider="openrouter",
        status=GenerationStatus.FAILED,
        idempotency_key="provider-health-test",
        error_code="PROVIDER_ERROR",
        error_message="rate limit",
        completed_at=datetime.now(timezone.utc),
    )
    db.add(job)
    db.commit()

    health = collect_ai_provider_health(db)
    assert health["configured"] is True
    assert health["failed_jobs"] == 1
    assert health["alert"] is True
    assert health["alert_reason"] == "generation_failures"
    assert health["latest_failure"]["error_code"] == "PROVIDER_ERROR"


def test_provider_health_endpoint_is_authenticated_and_secret_free(client, api, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "openrouter")
    monkeypatch.setattr(settings, "openrouter_api_key", "test-openrouter-key")

    unauthorized = client.get(f"{api}/generation/health")
    assert unauthorized.status_code in {401, 403}

    response = client.get(f"{api}/generation/health", headers=auth_headers)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["provider"] == "openrouter"
    assert "openrouter_api_key" not in payload
    assert "test-openrouter-key" not in response.text
