def test_creative_capability_catalog_is_local_and_platform_aware(client, api, auth_headers):
    response = client.get(f"{api}/organizations/creative-capabilities", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["platforms"] == ["facebook", "instagram", "linkedin"]
    assert "human_approval" in payload["quality_gates"]
    assert any(item["name"] == "service-announcement" for item in payload["archetypes"])


def test_pamphlet_brief_requires_accessibility_text_when_qr_is_present(client, api, auth_headers):
    organization_response = client.post(
        f"{api}/organizations/",
        headers=auth_headers,
        json={"name": "Pamphlet Workspace", "slug": "pamphlet-workspace"},
    )
    assert organization_response.status_code == 201, organization_response.text
    organization_id = organization_response.json()["id"]
    response = client.post(
        f"{api}/organizations/pamphlets?organization_id={organization_id}",
        headers=auth_headers,
        json={"title": "Service brochure", "qr_url": "https://example.com/book"},
    )
    assert response.status_code == 422
    assert "accessibility_text" in response.text


def test_pamphlet_brief_is_created_as_approval_required_draft(client, api, auth_headers):
    organization_response = client.post(
        f"{api}/organizations/",
        headers=auth_headers,
        json={"name": "Print Workspace", "slug": "print-workspace"},
    )
    assert organization_response.status_code == 201, organization_response.text
    organization_id = organization_response.json()["id"]
    response = client.post(
        f"{api}/organizations/pamphlets?organization_id={organization_id}",
        headers=auth_headers,
        json={
            "title": "A4 tri-fold service brochure",
            "objective": "conversion",
            "fold_style": "tri-fold",
            "qr_url": "https://example.com/book",
            "accessibility_text": "A tri-fold brochure describing the workspace services and contact CTA.",
            "content": {"panels": [{"role": "cover"}, {"role": "services"}, {"role": "contact"}]},
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["status"] == "draft"
    assert payload["approval_required"] is True
    assert payload["fold_style"] == "tri-fold"
    assert payload["bleed_mm"] == 3
