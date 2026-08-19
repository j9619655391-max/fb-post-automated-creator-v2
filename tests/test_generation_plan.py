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
