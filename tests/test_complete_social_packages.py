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
        image_text="The Occasion Edit — made for your moment",
        alt_text="A branded occasion-wear creative for The Occasion Edit.",
        objective="product discovery",
        creative_archetype="collection-story",
        source_refs=["approved-source: https://example.com/style"],
        claim_refs=["claim: handcrafted details"],
        visual_brief={"template_family": "collection-story", "safe_area": "left-panel"},
        asset_provenance={"mode": "workspace_media", "source_media_id": 44},
        visual_qa_status="passed",
        visual_qa_flags=[],
    )

    assert len(packages) == 3
    instagram = next(package for package in packages if package.platform == "instagram")
    payload = content_package_payload(instagram)
    assert payload["caption"].startswith("The Occasion Edit")
    assert payload["image_text"] == "The Occasion Edit — made for your moment"
    assert payload["alt_text"].startswith("A branded occasion-wear")
    assert payload["objective"] == "product discovery"
    assert payload["creative_archetype"] == "collection-story"
    assert payload["source_refs"] == ["approved-source: https://example.com/style"]
    assert payload["claim_refs"] == ["claim: handcrafted details"]
    assert payload["visual_brief"]["safe_area"] == "left-panel"
    assert payload["asset_provenance"]["mode"] == "workspace_media"
    assert payload["visual_qa_status"] == "passed"
    assert payload["visual_qa_flags"] == []
    assert payload["cta"] == "Book a consultation"
    assert payload["hashtags"] == ["#fashion", "#tailoring", "#Kashvera"]
    assert payload["tags"] == ["@kashverafashion", "occasion wear"]
    assert payload["media_variant_ids"] == [102]
    assert instagram.status == "draft"
    assert json.loads(instagram.tags_json) == ["@kashverafashion", "occasion wear"]
    assert db.query(ContentPackage).count() == 3
