import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.content import Content
from app.models.content_opportunity import ContentOpportunity
from app.models.content_package import ContentPackage
from app.models.brand_theme import BrandTheme


_ALLOWED_PLATFORMS = {"facebook", "instagram", "linkedin"}


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


def _adapt_caption(content: Content, platform: str, opportunity: ContentOpportunity | None) -> str:
    body = (content.body or "").strip()
    source_note = f"\n\nSource for review: {opportunity.source_url}" if opportunity and opportunity.source_url else ""
    if platform == "linkedin":
        return f"{content.title}\n\n{body}{source_note}"
    if platform == "instagram":
        return f"{content.title}\n\n{body}\n\nShare this with someone who needs it.{source_note}"
    return f"{content.title}\n\n{body}{source_note}"


def create_content_packages(
    db: Session,
    content_id: int,
    organization_id: int,
    platforms: list[str],
    theme_id: int | None = None,
    opportunity_id: int | None = None,
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
        package.caption = _adapt_caption(content, platform, opportunity)
        package.cta = "Learn more" if platform == "linkedin" else "Tell us what you think"
        package.hashtags_json = json.dumps([f"#{platform}"])
        package.source_urls_json = json.dumps(_source_urls(opportunity))
        package.media_variant_ids_json = json.dumps([])
        package.status = "draft"
        packages.append(package)
    db.commit()
    for package in packages:
        db.refresh(package)
    return packages
