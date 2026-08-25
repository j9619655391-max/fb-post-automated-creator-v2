import json

from app.models.content import Content, ContentStatus
from app.models.content_package import ContentPackage
from app.models.organization import Organization
from app.models.user import User
from app.services.content_package_service import content_package_payload, create_content_packages


def test_complete_social_package_metadata_is_preserved(db):
    user = User(
        username="package-owner",
        email="package-owner@example.com",
        full_name="Package Owner",
        hashed_password="not-a-real-password-hash",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    organization = Organization(
        name="Fashion Package Workspace",
        slug="fashion-package-workspace",
        created_by_id=user.id,
    )
    db.add(organization)
    db.commit()
    db.refresh(organization)

    content = Content(
        title="The Occasion Edit",
        body="A style note for your next occasion.",
        status=ContentStatus.DRAFT,
        organization_id=organization.id,
        created_by_id=user.id,
    )
    db.add(content)
    db.commit()
    db.refresh(content)

    packages = create_content_packages(
        db,
        content.id,
        organization.id,
        ["facebook", "instagram", "linkedin"],
        caption="A style note for your next occasion. Message us to discuss your look.",
        cta="Book a consultation",
        hashtags=["fashion", "tailoring", "Kashvera"],
        tags=["@kashverafashion", "occasion wear"],
        media_variant_ids_by_platform={
            "facebook": [101],
            "instagram": [102],
            "linkedin": [103],
        },
    )

    assert len(packages) == 3
    instagram = next(package for package in packages if package.platform == "instagram")
    payload = content_package_payload(instagram)
    assert payload["caption"].startswith("The Occasion Edit")
    assert payload["cta"] == "Book a consultation"
    assert payload["hashtags"] == ["#fashion", "#tailoring", "#Kashvera"]
    assert payload["tags"] == ["@kashverafashion", "occasion wear"]
    assert payload["media_variant_ids"] == [102]
    assert instagram.status == "draft"
    assert json.loads(instagram.tags_json) == ["@kashverafashion", "occasion wear"]
    assert db.query(ContentPackage).count() == 3
