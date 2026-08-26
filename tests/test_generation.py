from app.models.content_generation_usage import ContentGenerationUsage
from app.core.config import settings
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
        expected_model = settings.gemini_model if settings.ai_provider == "gemini" else settings.openrouter_model
        assert model == expected_model

        assert "morning" in contents
        return FakeGenerationResponse()


class FakeGenerationClient:
    models = FakeModels()

    def close(self):
        pass


def test_generate_complete_draft_persists_provenance_and_usage(client, api, auth_headers, monkeypatch):
    organization_response = client.post(
        f"{api}/organizations/",
        headers=auth_headers,
        json={"name": "Generation Workspace", "slug": "generation-workspace"},
    )
    assert organization_response.status_code == 201, organization_response.text
    organization_id = organization_response.json()["id"]

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
            "organization_id": organization_id,
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
        if settings.ai_provider == "openrouter":
            assert usage.cost_usd == 0
        else:
            assert usage.cost_usd > 0

    finally:
        db.close()


def test_generate_draft_requires_authentication(client, api):
    response = client.post(
        f"{api}/generation/draft",
        json={"category_name": "Motivation"},
    )
    assert response.status_code == 401


def test_org_generation_quota_blocks_provider_call(db, monkeypatch):
    from pytest import raises
    from app.models.content_generation import ContentGenerationJob, GenerationStatus
    from app.models.content_generation_usage import ContentGenerationUsage
    from app.models.organization import Organization, OrganizationMember, OrganizationRole
    from app.models.user import User
    from app.services.content_generation_service import GenerationQuotaExceeded

    user = User(
        username="quota-user",
        email="quota-user@example.com",
        full_name="Quota User",
        hashed_password="not-a-real-password-hash",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    organization = Organization(
        name="Quota Workspace",
        slug="quota-workspace",
        created_by_id=user.id,
    )
    db.add(organization)
    db.commit()
    db.refresh(organization)
    db.add(OrganizationMember(
        organization_id=organization.id,
        user_id=user.id,
        role=OrganizationRole.OWNER,
    ))

    job = ContentGenerationJob(
        organization_id=organization.id,
        requested_by_id=user.id,
        category_name="Motivation",
        model="gemini-2.5-flash",
        provider="gemini",
        status=GenerationStatus.SUCCEEDED,
        idempotency_key="quota-seed-001",
    )
    db.add(job)
    db.flush()
    db.add(ContentGenerationUsage(
        generation_job_id=job.id,
        organization_id=organization.id,
        requested_by_id=user.id,
        provider="gemini",
        model="gemini-2.5-flash",
        total_token_count=150,
    ))
    db.commit()

    monkeypatch.setattr(
        "app.services.settings_service.SettingsService.get_ai_quota_limits",
        lambda _self, _tier: {
            "max_ai_requests_per_month": 1,
            "max_ai_tokens_per_month": 100_000,
        },
    )
    monkeypatch.setattr(
        content_generation_service,
        "get_client",
        lambda: (_ for _ in ()).throw(AssertionError("provider must not be called")),
    )

    with raises(GenerationQuotaExceeded, match="Monthly AI requests quota exceeded"):
        content_generation_service.generate_and_persist_draft(
            db,
            user.id,
            category_name="Motivation",
            organization_id=organization.id,
            idempotency_key="quota-request-001",
        )
