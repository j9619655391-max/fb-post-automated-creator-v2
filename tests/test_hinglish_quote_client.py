import json

from app.models.organization import Organization
from app.models.user import User
from app.services.org_service import OrgService
from app.services.vce_service import get_recommended_category, list_categories
from app.services import content_generation_service
from app.core.config import settings
from scripts.init_db import _seed_categories


def test_quote_workspace_bootstraps_hinglish_profile_and_categories(db):
    user = User(
        username="quote-owner",
        email="quote-owner@example.com",
        full_name="Quote Owner",
        hashed_password="not-a-real-password-hash",
    )
    db.add(user)
    db.flush()

    _seed_categories(db)
    db.commit()
    organization = OrgService(db).create_organization(
        "Love, Truth, Motivational, Pain Quotes",
        "love-truth-motivational-pain-quotes",
        user.id,
    )

    db.refresh(organization)
    profile = organization.workspace_profile
    assert profile is not None
    assert "Hinglish" in json.loads(profile.preferred_languages_json)
    assert "Love quotes" in json.loads(profile.products_json)
    assert profile.approval_required is True

    category, reason, evidence = get_recommended_category(db, organization.id)
    assert category is not None
    assert category.slug in {"love-quotes", "truth-quotes", "motivational-quotes", "pain-quotes"}
    assert "Love, Truth, Motivational, Pain Quotes" in reason
    assert evidence

    slugs = {item.slug for item in list_categories(db, organization.id)}
    assert {"love-quotes", "truth-quotes", "motivational-quotes", "pain-quotes"}.issubset(slugs)


def test_quote_generation_prompt_enables_hinglish_and_quote_rules(db, monkeypatch):
    user = User(
        username="quote-prompt-owner",
        email="quote-prompt-owner@example.com",
        full_name="Quote Prompt Owner",
        hashed_password="not-a-real-password-hash",
    )
    db.add(user)
    db.flush()
    _seed_categories(db)
    db.commit()
    organization = OrgService(db).create_organization(
        "Love, Truth, Motivational, Pain Quotes",
        "love-truth-motivational-pain-quotes-prompt",
        user.id,
    )

    captured = {}

    class FakeUsage:
        prompt_token_count = 10
        candidates_token_count = 20
        thoughts_token_count = 0
        cached_content_token_count = 0
        total_token_count = 30

    class FakeResponse:
        text = (
            '{"title":"Sach ko chuno",'
            '"body":"Jo dil ko sach lage, usey imaandari se jeeyo.",'
            '"hook":"Zindagi ka sach:",'
            '"call_to_action":"Agar relate karte ho, share karo.",'
            '"hashtags":["#hinglishquotes"],"risk_flags":[]}'
        )
        usage_metadata = FakeUsage()

    class FakeModels:
        def generate_content(self, model: str, contents: str):
            captured["model"] = model
            captured["prompt"] = contents
            return FakeResponse()

    class FakeClient:
        models = FakeModels()

        def close(self):
            pass

    monkeypatch.setattr(content_generation_service, "get_client", lambda: FakeClient())
    job = content_generation_service.generate_and_persist_draft(
        db,
        user.id,
        category_name="Truth Quotes",
        organization_id=organization.id,
        idempotency_key="hinglish-prompt-test-001",
    )

    assert job.status.value == "succeeded"
    prompt = captured["prompt"]
    assert "HINGLISH_MODE: enabled" in prompt
    assert "natural Hinglish using Roman Hindi" in prompt
    assert "Love Quotes, Truth Quotes, Motivational Quotes, or Pain Quotes" in prompt
    assert "quote text the main creative idea" in prompt
