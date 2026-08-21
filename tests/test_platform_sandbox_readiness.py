from app.core.config import settings


def test_sandbox_readiness_reports_missing_provider_configuration(db, monkeypatch):
    from app.services.platform_sandbox_readiness_service import collect_platform_sandbox_readiness

    for name in (
        "facebook_app_id",
        "facebook_app_secret",
        "facebook_redirect_uri",
        "linkedin_client_id",
        "linkedin_client_secret",
        "linkedin_redirect_uri",
        "token_encryption_key",
    ):
        monkeypatch.setattr(settings, name, None)

    result = collect_platform_sandbox_readiness(db, user_id=999)
    assert result["publishing_attempted"] is False
    assert result["facebook"]["configured"] is False
    assert result["facebook"]["remote_check"] == "not_run"
    assert result["facebook"]["publish_ready"] is False
    assert result["instagram"]["publish_ready"] is False
    assert result["linkedin"]["configured"] is False
    assert result["linkedin"]["remote_check"] == "not_run"


def test_sandbox_readiness_endpoint_requires_authentication(client, api):
    response = client.get(f"{api}/platforms/sandbox-readiness")
    assert response.status_code in {401, 403}
