import json
from pathlib import Path
from typing import Any

from PIL import Image
from sqlalchemy.orm import Session

from app.models.content import Content
from app.models.content_opportunity import ContentOpportunity
from app.models.media import Media
from app.models.content_package import ContentPackage
from app.models.brand_theme import BrandTheme
from app.services.media_composer_service import FORMAT_SIZES


_ALLOWED_PLATFORMS = {"facebook", "instagram", "linkedin"}


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
    return [f"#{platform}", "#fashion", "#style"]


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
    visual_brief: dict[str, Any] | None = None,
    asset_provenance: dict[str, Any] | None = None,
    visual_qa_status: str = "not_run",
    visual_qa_flags: list[str] | None = None,
) -> list[ContentPackage]:
    content = db.query(Content).filter(Content.id == content_id, Content.organization_id == organization_id).first()
    if not content:
        raise ValueError("Content not found in this workspace")
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
        package.objective = _bounded_text(objective, 120) or None
        package.creative_archetype = _bounded_text(creative_archetype, 120) or None
        package.hashtags_json = json.dumps(_normalize_hashtags(hashtags, platform))
        package.tags_json = json.dumps(_normalize_items(tags))
        package.source_urls_json = json.dumps(_source_urls(opportunity))
        package.source_refs_json = json.dumps(_normalize_items(source_refs))
        package.claim_refs_json = json.dumps(_normalize_items(claim_refs))
        variant_ids = (media_variant_ids_by_platform or {}).get(platform, [])
        qa_status = visual_qa_status
        qa_flags = _normalize_items(visual_qa_flags)
        if visual_qa_status == "not_run" and variant_ids:
            qa_status, qa_flags = _structural_visual_qa(db, organization_id, platform, variant_ids)
        package.visual_brief_json = json.dumps({
            "platform": platform,
            "image_text_separate": True,
            "qa_scope": "asset_presence_and_dimensions_only",
            **(visual_brief or {}),
        })
        package.asset_provenance_json = json.dumps({
            "mode": "workspace_media" if variant_ids else "not_available",
            "media_variant_ids": variant_ids,
            **(asset_provenance or {}),
        })
        package.media_variant_ids_json = json.dumps(variant_ids)
        package.visual_qa_status = _bounded_text(qa_status, 30, fallback="not_run") or "not_run"
        package.visual_qa_flags_json = json.dumps(qa_flags)
        package.status = "draft"
        packages.append(package)
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
        "visual_brief": _json_value(package.visual_brief_json, {}),
        "asset_provenance": _json_value(package.asset_provenance_json, {}),
        "media_variant_ids": [int(value) for value in _json_list(package.media_variant_ids_json) if value.isdigit()],
        "visual_qa_status": package.visual_qa_status,
        "visual_qa_flags": _json_list(package.visual_qa_flags_json),
        "status": package.status,
        "created_at": package.created_at,
        "updated_at": package.updated_at,
    }
