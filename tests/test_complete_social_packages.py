import json

import pytest
from PIL import Image

from app.models.content import Content, ContentStatus
from app.models.content_package import ContentPackage
from app.models.media import Media
from app.models.organization import Organization
from app.models.user import User
from app.services.content_package_service import content_package_payload, create_content_packages
from app.services.media_composer_service import FORMAT_SIZES


def test_complete_social_package_metadata_is_preserved(db, tmp_path):
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

    media_variant_ids_by_platform = {}
    for platform, size in FORMAT_SIZES.items():
        path = tmp_path / f"{platform}.png"
        Image.new("RGB", size, (64, 80, 96)).save(path, format="PNG")
        media = Media(
            filename=f"{platform}.png",
            stored_path=str(path),
            mime_type="image/png",
            file_size=path.stat().st_size,
            organization_id=organization.id,
            user_id=user.id,
        )
        db.add(media)
        db.flush()
        media_variant_ids_by_platform[platform] = [media.id]
    db.commit()

    packages = create_content_packages(
        db,
        content.id,
        organization.id,
        ["facebook", "instagram", "linkedin"],
        caption="A style note for your next occasion. Message us to discuss your look.",
        cta="Book a consultation",
        hashtags=["fashion", "tailoring", "Kashvera"],
        tags=["@kashverafashion", "occasion wear"],
        media_variant_ids_by_platform=media_variant_ids_by_platform,
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
    assert payload["visual_qa_status"] == "structural_pass"
    assert payload["visual_qa_flags"] == []
    assert payload["cta"] == "Book a consultation"
    assert payload["hashtags"] == ["#fashion", "#tailoring", "#Kashvera"]
    assert payload["tags"] == ["@kashverafashion", "occasion wear"]
    assert payload["media_variant_ids"] == media_variant_ids_by_platform["instagram"]
    assert instagram.status == "draft"
    assert json.loads(instagram.tags_json) == ["@kashverafashion", "occasion wear"]
    assert db.query(ContentPackage).count() == 3


def test_package_intent_metadata_rejects_unsupported_values(db):
    user = User(
        username="package-intent-owner",
        email="package-intent-owner@example.com",
        full_name="Package Intent Owner",
        hashed_password="not-a-real-password-hash",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    organization = Organization(name="Intent Workspace", slug="intent-workspace", created_by_id=user.id)
    db.add(organization)
    db.commit()
    db.refresh(organization)
    content = Content(
        title="Intent test",
        body="Intent body",
        status=ContentStatus.DRAFT,
        organization_id=organization.id,
        created_by_id=user.id,
    )
    db.add(content)
    db.commit()
    db.refresh(content)

    with pytest.raises(ValueError, match="Unsupported objective"):
        create_content_packages(
            db,
            content.id,
            organization.id,
            ["facebook"],
            objective="unsupported-objective",
        )


def test_text_only_workspace_package_is_rejected(db):
    user = User(
        username="image-required-owner",
        email="image-required-owner@example.com",
        full_name="Image Required Owner",
        hashed_password="not-a-real-password-hash",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    organization = Organization(name="Image Required Workspace", slug="image-required-workspace", created_by_id=user.id)
    db.add(organization)
    db.commit()
    db.refresh(organization)
    content = Content(
        title="Text only draft",
        body="This must not become a publishable workspace package without images.",
        status=ContentStatus.DRAFT,
        organization_id=organization.id,
        created_by_id=user.id,
    )
    db.add(content)
    db.commit()
    db.refresh(content)

    with pytest.raises(ValueError, match="Image variant required"):
        create_content_packages(db, content.id, organization.id, ["facebook"])

