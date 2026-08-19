def test_list_content_requires_authentication(client, api):
    response = client.get(f"{api}/content/")
    assert response.status_code == 401


def test_list_content_authenticated_user(client, api, auth_headers):
    response = client.get(f"{api}/content/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_vce_share_psychology_tips(client, api, auth_headers):
    """VCE share-psychology-tips returns advisory tips."""
    response = client.get(f"{api}/vce/share-psychology-tips", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data.get("advisory_only") is True
    assert isinstance(data.get("tips"), list)
    assert len(data["tips"]) >= 1
    tip = data["tips"][0]
    assert {"id", "title", "tip"}.issubset(tip)


def test_vce_categories(client, api, auth_headers):
    """VCE categories returns a list, empty when the database is not seeded."""
    response = client.get(f"{api}/vce/categories", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_vce_categories_today(client, api, auth_headers):
    """Today's category returns a category or 404 when none are seeded."""
    response = client.get(f"{api}/vce/categories/today", headers=auth_headers)
    assert response.status_code in (200, 404)
