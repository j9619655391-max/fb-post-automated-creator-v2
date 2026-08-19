from decimal import Decimal

from app.core.database import SessionLocal
from app.models.content_generation import ContentGenerationJob, GenerationStatus
from app.models.content_generation_usage import ContentGenerationUsage
from app.models.organization import Organization, OrganizationMember, OrganizationRole
from app.models.user import User


def test_billing_usage_returns_org_token_and_cost_totals(client, api, auth_headers):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "test-user").one()
        org = Organization(name="Usage Org", slug="usage-org", created_by_id=user.id)
        db.add(org)
        db.flush()
        db.add(OrganizationMember(organization_id=org.id, user_id=user.id, role=OrganizationRole.OWNER))
        job = ContentGenerationJob(
            organization_id=org.id,
            requested_by_id=user.id,
            provider="google",
            model="gemini-test",
            status=GenerationStatus.SUCCEEDED,
        )
        db.add(job)
        db.flush()
        db.add(ContentGenerationUsage(
            generation_job_id=job.id,
            organization_id=org.id,
            requested_by_id=user.id,
            provider="google",
            model="gemini-test",
            prompt_token_count=100,
            candidates_token_count=50,
            total_token_count=150,
            cost_usd=Decimal("0.01250000"),
        ))
        db.commit()
        org_id = org.id
    finally:
        db.close()

    response = client.get(f"{api}/billing/usage", params={"organization_id": org_id}, headers=auth_headers)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["requests"] == 1
    assert payload["prompt_tokens"] == 100
    assert payload["total_tokens"] == 150
    assert payload["estimated_cost_usd"] == 0.0125
    assert payload["by_model"][0]["model"] == "gemini-test"
