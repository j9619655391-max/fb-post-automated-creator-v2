from app.models.content_generation_usage import ContentGenerationUsage
from app.services import content_generation_service


class FakeUsage:
    prompt_token_count = 100
    candidates_token_count = 50
    thoughts_token_count = 0
    cached_content_token_count = 0
    total_token_count = 150


class FakeGenerationResponse:
    text = (
        '{"title":"A better morning routine",'
        '"body":"Small habits compound over time.",'
        '"hook":"What would you change first?",'
        '"call_to_action":"Share your best habit.",'
        '"hashtags":["#habits"],'
        '"risk_flags":[]}'
    )
    usage_metadata = FakeUsage()


class FakeModels:
    def generate_content(self, model: str, contents: str):
        assert model == "gemini-2.5-flash"
        assert "morning" in contents
        return FakeGenerationResponse()


class FakeGenerationClient:
    models = FakeModels()

    def close(self):
        pass


def test_generate_complete_draft_persists_provenance_and_usage(client, api, auth_headers, monkeypatch):
    monkeypatch.setattr(
        content_generation_service,
        "get_client",
        lambda: FakeGenerationClient(),
    )

    response = client.post(
        f"{api}/generation/draft",
        headers=auth_headers,
        json={
            "category_name": "Motivation",
            "extra_instruction": "Focus on practical morning habits.",
            "idempotency_key": "generation-test-001",
        },
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["title"] == "A better morning routine"
    assert data["status"] == "draft"
    assert data["generated_by_ai"] is True
    assert data["generation_job_id"] is not None

    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        usage = db.query(ContentGenerationUsage).one()
        assert usage.prompt_token_count == 100
        assert usage.candidates_token_count == 50
        assert usage.total_token_count == 150
        assert usage.cost_usd > 0
    finally:
        db.close()


def test_generate_draft_requires_authentication(client, api):
    response = client.post(
        f"{api}/generation/draft",
        json={"category_name": "Motivation"},
    )
    assert response.status_code == 401
