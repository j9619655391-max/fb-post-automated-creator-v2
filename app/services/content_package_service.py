import json
from pathlib import Path
from typing import Any

from PIL import Image
from sqlalchemy.orm import Session

from app.models.content import Content
from app.models.content_opportunity import ContentOpportunity
from app.models.media import Media
from app.models.content_package import ContentPackage
from app.models.workspace_evidence import ContentPackageEvidence, WorkspaceClaim
from app.models.workspace_intelligence import WorkspaceSource
from app.models.brand_theme import BrandTheme
from app.services.media_composer_service import FORMAT_SIZES


_ALLOWED_PLATFORMS = {"facebook", "instagram", "linkedin"}
_ALLOWED_OBJECTIVES = {"awareness", "education", "product discovery", "conversion", "lead generation", "proof", "community"}
_ALLOWED_ARCHETYPES = {
    "service-announcement",
    "fashion-editorial",
    "technology-explainer",
    "product-showcase",
    "quote-card",
    "collection-story",
    "educational-explainer",
    "offer-card",
    "case-study-proof",
    "customer-story",
    "behind-the-scenes",
    "seasonal-campaign",
}
_ALLOWED_ASSET_MODES = {"workspace_media", "branded_text_card", "deterministic_text_card", "ai_generated", "stock_licensed", "not_available"}


def _validate_choice(value: str | None, allowed: set[str], label: str) -> str | None:
    normalized = " ".join(str(value or "").split()).strip()
    if normalized and normalized not in allowed:
        raise ValueError(f"Unsupported {label}: {normalized}")
    return normalized or None


def _validate_evidence_ids(
    db: Session,
    organization_id: int,
    source_ids: list[int] | None,
    claim_ids: list[int] | None,
) -> tuple[list[int], list[int], str]:
    normalized_sources = list(dict.fromkeys(int(value) for value in (source_ids or []) if int(value) > 0))[:40]
    normalized_claims = list(dict.fromkeys(int(value) for value in (claim_ids or []) if int(value) > 0))[:40]
    if normalized_sources:
        sources = db.query(WorkspaceSource).filter(
            WorkspaceSource.organization_id == organization_id,
            WorkspaceSource.id.in_(normalized_sources),
            WorkspaceSource.is_active.is_(True),
            WorkspaceSource.review_status == "approved",
        ).all()
        if {source.id for source in sources} != set(normalized_sources):
            raise ValueError("Every source_ref_id must belong to an active approved workspace source")
    if normalized_claims:
        claims = db.query(WorkspaceClaim).filter(
            WorkspaceClaim.organization_id == organization_id,
            WorkspaceClaim.id.in_(normalized_claims),
            WorkspaceClaim.review_status == "approved",
        ).all()
        if {claim.id for claim in claims} != set(normalized_claims):
            raise ValueError("Every claim_ref_id must belong to an approved workspace claim")
    if normalized_sources or normalized_claims:
        return normalized_sources, normalized_claims, "verified"
    return [], [], "unverified"


def _structural_visual_qa(db: Session, organization_id: int, platform: str, media_ids: list[int]) -> tuple[str, list[str]]:
    """Validate asset presence and exact platform dimensions only.

    This is an automated structural gate, not a replacement for human creative
    review or browser-level readability inspection.
    """
    if not media_ids:
        return "failed", ["missing_media_variant"]
    expected = FORMAT_SIZES.get(platform)
    flags: list[str] = []
    for media_id in media_ids:
        media = db.query(Media).filter(Media.id == media_id, Media.organization_id == organization_id).first()
        if not media or not media.stored_path or not Path(media.stored_path).exists():
            flags.append("media_not_found")
            continue
        try:
            with Image.open(media.stored_path) as image:
                if expected and image.size != expected:
                    flags.append(f"unexpected_dimensions:{image.size[0]}x{image.size[1]}")
        except (OSError, ValueError):
            flags.append("media_unreadable")
    return ("structural_pass" if not flags else "failed"), list(dict.fromkeys(flags))


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _source_urls(opportunity: ContentOpportunity | None) -> list[str]:
    if not opportunity:
        return []
    return [opportunity.source_url] if opportunity.source_url else []


def _json_value(value: str | None, fallback: Any = None) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _bounded_text(value: str | None, limit: int, fallback: str = "") -> str:
    text = " ".join(str(value or fallback).split()).strip()
    return text[:limit]


def _adapt_caption(
    content: Content,
    platform: str,
    opportunity: ContentOpportunity | None,
    caption: str | None = None,
) -> str:
    body = (caption or content.body or "").strip()
    source_note = f"\n\nSource for review: {opportunity.source_url}" if opportunity and opportunity.source_url else ""
    if platform == "linkedin":
        return f"{content.title}\n\n{body}{source_note}"
    if platform == "instagram":
        return f"{content.title}\n\n{body}\n\nShare this with someone who needs it.{source_note}"
    return f"{content.title}\n\n{body}{source_note}"


def _normalize_items(values: list[str] | None) -> list[str]:
    return list(dict.fromkeys(str(value).strip() for value in (values or []) if str(value).strip()))[:40]


def _normalize_hashtags(values: list[str] | None, platform: str) -> list[str]:
    supplied = _normalize_items(values)
    if supplied:
        return [value if value.startswith("#") else f"#{value.lstrip('#')}" for value in supplied]
    return [f"#{platform}", "#business", "#socialmedia"]


def create_content_packages(
    db: Session,
    content_id: int,
    organization_id: int,
    platforms: list[str],
    theme_id: int | None = None,
    opportunity_id: int | None = None,
    *,
    caption: str | None = None,
    cta: str | None = None,
    hashtags: list[str] | None = None,
    tags: list[str] | None = None,
    media_variant_ids_by_platform: dict[str, list[int]] | None = None,
    image_text: str | None = None,
    alt_text: str | None = None,
    objective: str | None = None,
    creative_archetype: str | None = None,
    source_refs: list[str] | None = None,
    claim_refs: list[str] | None = None,
    source_ref_ids: list[int] | None = None,
    claim_ref_ids: list[int] | None = None,
    visual_brief: dict[str, Any] | None = None,
    asset_provenance: dict[str, Any] | None = None,
    visual_qa_status: str = "not_run",
    visual_qa_flags: list[str] | None = None,
) -> list[ContentPackage]:
    content = db.query(Content).filter(Content.id == content_id, Content.organization_id == organization_id).first()
    if not content:
        raise ValueError("Content not found in this workspace")
    if not organization_id:
        raise ValueError("Image-first packages require a workspace")
    normalized = list(dict.fromkeys(platform.lower() for platform in platforms))
    if not normalized or any(platform not in _ALLOWED_PLATFORMS for platform in normalized):
        raise ValueError("Platforms must be facebook, instagram, or linkedin")
    theme = None
    if theme_id:
        theme = db.query(BrandTheme).filter(BrandTheme.id == theme_id, BrandTheme.organization_id == organization_id, BrandTheme.is_active.is_(True)).first()
        if not theme:
            raise ValueError("Theme not found in this workspace")
    opportunity = None
    if opportunity_id:
        opportunity = db.query(ContentOpportunity).filter(ContentOpportunity.id == opportunity_id, ContentOpportunity.organization_id == organization_id).first()
        if not opportunity:
            raise ValueError("Opportunity not found in this workspace")
    validated_source_ids, validated_claim_ids, evidence_status = _validate_evidence_ids(
        db, organization_id, source_ref_ids, claim_ref_ids
    )
    packages: list[ContentPackage] = []
    for platform in normalized:
        package = db.query(ContentPackage).filter(ContentPackage.source_content_id == content.id, ContentPackage.platform == platform).first()
        if package is None:
            package = ContentPackage(organization_id=organization_id, source_content_id=content.id, platform=platform)
            db.add(package)
        package.theme_id = theme.id if theme else None
        package.opportunity_id = opportunity.id if opportunity else None
        package.headline = content.title
        package.image_text = _bounded_text(image_text, 160, fallback=content.title)
        package.caption = _adapt_caption(content, platform, opportunity, caption)
        package.alt_text = _bounded_text(alt_text, 500, fallback=f"{content.title}. {package.image_text}")
        package.cta = cta or ("Book a consultation" if platform == "linkedin" else "Send us a message")
        package.objective = _validate_choice(_bounded_text(objective, 120), _ALLOWED_OBJECTIVES, "objective")
        package.creative_archetype = _validate_choice(_bounded_text(creative_archetype, 120), _ALLOWED_ARCHETYPES, "creative archetype")
        package.hashtags_json = json.dumps(_normalize_hashtags(hashtags, platform))
        package.tags_json = json.dumps(_normalize_items(tags))
        package.source_urls_json = json.dumps(_source_urls(opportunity))
        package.source_refs_json = json.dumps(_normalize_items(source_refs))
        package.claim_refs_json = json.dumps(_normalize_items(claim_refs))
        package.source_ref_ids_json = json.dumps(validated_source_ids)
        package.claim_ref_ids_json = json.dumps(validated_claim_ids)
        package.evidence_status = evidence_status
        variant_ids = list(dict.fromkeys(int(value) for value in (media_variant_ids_by_platform or {}).get(platform, []) if int(value) > 0))
        if not variant_ids:
            raise ValueError(f"Image variant required for {platform} image-first package")
        requested_qa_flags = _normalize_items(visual_qa_flags)
        structural_status, structural_flags = _structural_visual_qa(db, organization_id, platform, variant_ids)
        qa_flags = list(dict.fromkeys(requested_qa_flags + structural_flags))
        # The renderer/storage check is authoritative. A caller-supplied
        # `passed` or `not_run` value cannot bypass missing, unreadable, or
        # incorrectly sized platform images.
        qa_status = structural_status
        package.visual_brief_json = json.dumps({
            "platform": platform,
            "image_text_separate": True,
            "qa_scope": "asset_presence_and_dimensions_only",
            **(visual_brief or {}),
        })
        provenance = {
            "mode": "workspace_media" if variant_ids else "not_available",
            "media_variant_ids": variant_ids,
            **(asset_provenance or {}),
        }
        provenance["mode"] = _validate_choice(provenance.get("mode"), _ALLOWED_ASSET_MODES, "asset provenance mode") or "not_available"
        if provenance["mode"] == "not_available":
            raise ValueError(f"Asset provenance required for {platform} image-first package")
        package.asset_provenance_json = json.dumps(provenance)
        package.media_variant_ids_json = json.dumps(variant_ids)
        package.visual_qa_status = _bounded_text(qa_status, 30, fallback="not_run") or "not_run"
        package.visual_qa_flags_json = json.dumps(qa_flags)
        package.status = "draft"
        packages.append(package)
    db.flush()
    for package in packages:
        db.query(ContentPackageEvidence).filter(ContentPackageEvidence.content_package_id == package.id).delete(synchronize_session=False)
        for source_id in validated_source_ids:
            db.add(ContentPackageEvidence(content_package_id=package.id, source_id=source_id, evidence_type="source"))
        for claim_id in validated_claim_ids:
            db.add(ContentPackageEvidence(content_package_id=package.id, claim_id=claim_id, evidence_type="claim"))
    db.commit()
    for package in packages:
        db.refresh(package)
    return packages


def content_package_payload(package: ContentPackage) -> dict[str, Any]:
    return {
        "id": package.id,
        "organization_id": package.organization_id,
        "source_content_id": package.source_content_id,
        "theme_id": package.theme_id,
        "opportunity_id": package.opportunity_id,
        "platform": package.platform,
        "headline": package.headline,
        "image_text": package.image_text,
        "caption": package.caption,
        "alt_text": package.alt_text,
        "cta": package.cta,
        "objective": package.objective,
        "creative_archetype": package.creative_archetype,
        "hashtags": _json_list(package.hashtags_json),
        "tags": _json_list(package.tags_json),
        "source_urls": _json_list(package.source_urls_json),
        "source_refs": _json_value(package.source_refs_json, []),
        "claim_refs": _json_value(package.claim_refs_json, []),
        "source_ref_ids": [int(value) for value in _json_list(package.source_ref_ids_json) if value.isdigit()],
        "claim_ref_ids": [int(value) for value in _json_list(package.claim_ref_ids_json) if value.isdigit()],
        "evidence_status": package.evidence_status,
        "visual_brief": _json_value(package.visual_brief_json, {}),
        "asset_provenance": _json_value(package.asset_provenance_json, {}),
        "media_variant_ids": [int(value) for value in _json_list(package.media_variant_ids_json) if value.isdigit()],
        "visual_qa_status": package.visual_qa_status,
        "visual_qa_flags": _json_list(package.visual_qa_flags_json),
        "status": package.status,
        "created_at": package.created_at,
        "updated_at": package.updated_at,
    }
