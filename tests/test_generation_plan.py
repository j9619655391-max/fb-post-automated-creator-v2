from datetime import datetime, timedelta, timezone


def test_generation_plan_lifecycle(client, api, auth_headers):
    response = client.post(
        f"{api}/generation-plans/",
        headers=auth_headers,
        json={
            "name": "Daily motivation drafts",
            "category_name": "Motivation",
            "recurrence": "daily",
            "approval_mode": "required",
            "next_run_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        },
    )
    assert response.status_code == 201, response.text
    plan = response.json()
    assert plan["status"] == "active"
    assert plan["approval_mode"] == "required"

    listed = client.get(f"{api}/generation-plans/", headers=auth_headers)
    assert listed.status_code == 200
    assert any(item["id"] == plan["id"] for item in listed.json())

    paused = client.post(
        f"{api}/generation-plans/{plan['id']}/pause",
        headers=auth_headers,
    )
    assert paused.status_code == 200
    assert paused.json()["status"] == "paused"


def test_generation_plan_provider_failure_is_backed_off(db, monkeypatch):
    from app.models.generation_plan import ContentGenerationPlan, GenerationPlanStatus, GenerationRecurrence, ApprovalMode
    from app.services import generation_plan_service
    from app.services.content_generation_service import GenerationProviderError

    now = datetime.now(timezone.utc)
    plan = ContentGenerationPlan(
        created_by_id=1,
        name="Provider retry plan",
        category_name="Operations",
        recurrence=GenerationRecurrence.DAILY,
        approval_mode=ApprovalMode.REQUIRED,
        status=GenerationPlanStatus.ACTIVE,
        active=True,
        next_run_at=now - timedelta(minutes=1),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    def fail_generation(*args, **kwargs):
        raise GenerationProviderError(
            "OpenRouter request failed (429): rate limit exceeded",
            retryable=True,
            retry_after_seconds=720,
            provider="openrouter",
        )

    monkeypatch.setattr(generation_plan_service, "generate_and_persist_draft", fail_generation)
    result = generation_plan_service.run_due_plans(db, now=now)

    assert result == {"generated": 0, "failed": 1, "retry_scheduled": 1, "due": 1}
    refreshed = db.query(ContentGenerationPlan).filter(ContentGenerationPlan.id == plan.id).one()
    stored_next_run = refreshed.next_run_at
    if not stored_next_run.tzinfo:
        stored_next_run = stored_next_run.replace(tzinfo=timezone.utc)
    assert stored_next_run >= now + timedelta(seconds=720)
