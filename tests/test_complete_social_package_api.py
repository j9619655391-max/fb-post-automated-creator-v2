from PIL import Image

from app.models.media import Media
from app.models.user import User


def test_compose_package_returns_image_and_social_copy_per_platform(
    client, api, db, auth_headers, tmp_path
):
    organization_response = client.post(
        f"{api}/organizations/",
        headers=auth_headers,
        json={"name": "Studio Integration Workspace", "slug": "studio-integration-workspace"},
    )
    assert organization_response.status_code == 201, organization_response.text
    organization_id = organization_response.json()["id"]
    user = db.query(User).filter(User.username == "test-user").first()
    assert user is not None

    source_path = tmp_path / "fashion-source.jpg"
    Image.new("RGB", (900, 900), (32, 42, 50)).save(source_path, format="JPEG")
    source = Media(
        filename="fashion-source.jpg",
        stored_path=str(source_path),
        mime_type="image/jpeg",
        file_size=source_path.stat().st_size,
        organization_id=organization_id,
        user_id=user.id,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    response = client.post(
        f"{api}/organizations/{organization_id}/media/compose-package",
        headers=auth_headers,
        json={
            "source_media_id": source.id,
            "template_family": "quote-card",
            "headline": "Style is personal",
            "body": "The right detail makes the moment yours.",
            "caption": "A fashion thought for your next occasion.",
            "cta": "Book a consultation",
            "hashtags": ["fashion", "occasionwear"],
            "tags": ["@kashverafashion", "style community"],
            "platforms": ["facebook", "instagram", "linkedin"],
        },
    )

    assert response.status_code == 200, response.text
    packages = response.json()
    assert len(packages) == 3
    assert {package["platform"] for package in packages} == {"facebook", "instagram", "linkedin"}
    assert all(package["image"]["url"] for package in packages)
    assert all(package["caption"].startswith("Style is personal") for package in packages)
    assert all(package["hashtags"] == ["#fashion", "#occasionwear"] for package in packages)
    assert all(package["tags"] == ["@kashverafashion", "style community"] for package in packages)
    assert all(package["status"] == "draft" for package in packages)
    assert len({package["content_id"] for package in packages}) == 1
