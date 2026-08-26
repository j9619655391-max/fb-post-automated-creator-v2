import pytest
from PIL import Image

from app.models.content import Content, ContentStatus
from app.models.media import Media
from app.services.media_composer_service import FORMAT_SIZES
from app.models.content_package import ContentPackage
from app.models.organization import Organization
from app.models.user import User
from app.models.workspace_evidence import ContentPackageEvidence, WorkspaceClaim, WorkspaceClaimSource
from app.models.workspace_intelligence import WorkspaceSource
from app.services.content_package_service import content_package_payload, create_content_packages


def _workspace(db):
    user = User(username="evidence-owner", email="evidence-owner@example.com", full_name="Evidence Owner", hashed_password="test")
    db.add(user)
    db.commit()
    db.refresh(user)
    organization = Organization(name="Evidence Workspace", slug="evidence-workspace", created_by_id=user.id)
    db.add(organization)
    db.commit()
    db.refresh(organization)
    content = Content(title="Evidence creative", body="Grounded body", status=ContentStatus.DRAFT, organization_id=organization.id, created_by_id=user.id)
    db.add(content)
    db.commit()
    db.refresh(content)
    return user, organization, content


def test_only_approved_active_evidence_can_be_attached(db):
    _, organization, content = _workspace(db)
    pending_source = WorkspaceSource(
        organization_id=organization.id,
        source_type="manual",
        title="Pending source",
        review_status="pending",
        is_active=True,
    )
    db.add(pending_source)
    db.commit()
    db.refresh(pending_source)

    with pytest.raises(ValueError, match="active approved workspace source"):
        create_content_packages(db, content.id, organization.id, ["facebook"], source_ref_ids=[pending_source.id])


def test_verified_evidence_is_persisted_per_platform(db, tmp_path):
    _, organization, content = _workspace(db)
    source = WorkspaceSource(
        organization_id=organization.id,
        source_type="website",
        url="https://example.com/approved",
        title="Approved source",
        review_status="approved",
        is_active=True,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    claim = WorkspaceClaim(
        organization_id=organization.id,
        claim_text="The workspace provides verified services.",
        claim_type="service",
        review_status="approved",
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    db.add(WorkspaceClaimSource(claim_id=claim.id, source_id=source.id))
    db.commit()

    media_variant_ids_by_platform = {}
    for platform, size in FORMAT_SIZES.items():
        path = tmp_path / f"{platform}.png"
        Image.new("RGB", size, (32, 48, 64)).save(path, format="PNG")
        media = Media(
            filename=f"{platform}.png",
            stored_path=str(path),
            mime_type="image/png",
            file_size=path.stat().st_size,
            organization_id=organization.id,
            user_id=organization.created_by_id,
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
        source_ref_ids=[source.id],
        claim_ref_ids=[claim.id],
        media_variant_ids_by_platform=media_variant_ids_by_platform,
        asset_provenance={"mode": "workspace_media"},
    )

    assert len(packages) == 3
    assert all(package.evidence_status == "verified" for package in packages)
    assert db.query(ContentPackageEvidence).count() == 6
    payload = content_package_payload(packages[0])
    assert payload["source_ref_ids"] == [source.id]
    assert payload["claim_ref_ids"] == [claim.id]
    assert payload["evidence_status"] == "verified"
