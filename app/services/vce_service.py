"""Workspace-aware content categories and hook templates.

All suggestions are advisory; the operator remains in control of the final draft.
"""
from datetime import datetime, timezone
import re
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.content_category import ContentCategory
from app.models.hook_template import HookTemplate
from app.models.organization import Organization
from app.models.workspace_intelligence import WorkspaceProfile, WorkspaceSource


_CATEGORY_SIGNALS: dict[str, tuple[str, ...]] = {
    "product-showcase": ("fashion", "tailor", "tailoring", "boutique", "apparel", "suit", "garment", "designer", "product", "offer"),
    "collection-launch": ("fashion", "collection", "seasonal", "apparel", "designer", "launch"),
    "bridal-occasion": ("bridal", "wedding", "occasion", "partywear", "ceremony", "fashion"),
    "styling-tips": ("fashion", "styling", "wardrobe", "outfit", "suit", "apparel", "beauty"),
    "fabric-craft": ("fashion", "fabric", "craft", "tailor", "embroidery", "garment", "apparel"),
    "fashion-quote": ("fashion", "style", "wardrobe", "designer", "tailor"),
    "seasonal-festival": ("fashion", "festival", "seasonal", "holiday", "occasion"),
    "service-showcase": ("service", "solution", "agency", "consulting", "consultancy", "marketing", "digital", "software", "technology", "it", "jobs", "overseas", "education"),
    "case-study-results": ("case", "result", "client", "portfolio", "agency", "marketing", "solution", "consulting"),
    "educational-howto": ("education", "training", "guide", "how", "tips", "marketing", "technology", "software", "consulting", "student"),
    "industry-insights": ("industry", "insight", "research", "news", "marketing", "technology", "software", "digital", "finance", "jobs"),
    "client-story": ("client", "customer", "testimonial", "case", "service", "consulting", "agency"),
    "company-culture": ("team", "company", "culture", "hiring", "jobs", "organization"),
    "behind-the-scenes": ("behind", "process", "team", "craft", "studio", "agency", "fashion"),
    "offer-booking": ("offer", "booking", "consultation", "appointment", "service", "fashion", "marketing"),
    "love-quotes": ("love", "romance", "relationship", "ishq", "pyaar", "mohabbat", "quotes", "quote"),
    "truth-quotes": ("truth", "reality", "sach", "haqeeqat", "quotes", "quote"),
    "motivational-quotes": ("motivational", "motivation", "inspiration", "inspirational", "hustle", "growth", "quotes", "quote"),
    "pain-quotes": ("pain", "sad", "sadness", "healing", "heartbreak", "dard", "tanha", "quotes", "quote"),
}


def _workspace_signal_text(db: Session, organization_id: int | None) -> tuple[str, str]:
    if not organization_id:
        return "", ""
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    profile = db.query(WorkspaceProfile).filter(WorkspaceProfile.organization_id == organization_id).first()
    sources = (
        db.query(WorkspaceSource)
        .filter(WorkspaceSource.organization_id == organization_id, WorkspaceSource.is_active.is_(True))
        .order_by(WorkspaceSource.created_at.desc())
        .limit(12)
        .all()
    )
    name = organization.name if organization else ""
    parts = [name]
    if profile:
        parts.extend([
            profile.business_description or "",
            profile.industry or "",
            profile.target_audience or "",
            profile.mission or "",
            profile.tagline or "",
            " ".join(_json_list(profile.services_json)),
            " ".join(_json_list(profile.products_json)),
            " ".join(_json_list(profile.keywords_json)),
        ])
    parts.extend(source.title or source.excerpt or source.url or "" for source in sources)
    return " ".join(parts).lower(), name


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    import json
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _category_score(category: ContentCategory, signal_text: str) -> int:
    tokens = set(re.findall(r"[a-z0-9]+", signal_text))
    score = 0
    for signal in _CATEGORY_SIGNALS.get(category.slug, ()):
        if signal in tokens or signal in signal_text:
            score += 3 if len(signal) > 3 else 1
    if category.slug in {"motivation", "reflection"}:
        score -= 12
    if category.slug == "tips" and any(term in signal_text for term in ("marketing", "technology", "education", "fashion")):
        score += 2
    return score


def list_categories(db: Session, organization_id: int | None = None) -> List[ContentCategory]:
    """List categories with the best workspace fit first when a workspace is supplied."""
    categories = db.query(ContentCategory).order_by(ContentCategory.sort_order, ContentCategory.name).all()
    if not organization_id:
        return categories
    signal_text, _ = _workspace_signal_text(db, organization_id)
    return sorted(categories, key=lambda category: (-_category_score(category, signal_text), category.sort_order, category.name))


def get_recommended_category(db: Session, organization_id: int | None = None) -> tuple[Optional[ContentCategory], str, list[str]]:
    """Return the highest-fit category, explanation, and bounded evidence labels."""
    categories = list_categories(db, organization_id)
    if not categories:
        return None, "No categories are configured.", []
    if not organization_id:
        return categories[0], "Default category rotation is advisory until a workspace is selected.", []
    signal_text, workspace_name = _workspace_signal_text(db, organization_id)
    scored = sorted(((category, _category_score(category, signal_text)) for category in categories), key=lambda item: (-item[1], item[0].sort_order, item[0].name))
    category, score = scored[0]
    evidence_terms = [term for term in _CATEGORY_SIGNALS.get(category.slug, ()) if term in signal_text][:5]
    if score <= 0:
        category = next((item for item in categories if item.slug not in {"motivation", "reflection"}), categories[0])
        reason = f"No strong business signal was found for {workspace_name or 'this workspace'}; a neutral business category is suggested for review."
    else:
        reason = f"Suggested from {workspace_name or 'the selected workspace'} business profile and public source signals."
    return category, reason, evidence_terms


def get_rotated_category_for_today(db: Session, organization_id: int | None = None) -> Optional[ContentCategory]:
    """Return a workspace-aware category with date rotation as a tie-breaker."""
    categories = list_categories(db, organization_id)
    if not categories:
        return None
    today = datetime.now(timezone.utc)
    return categories[(today.timetuple().tm_yday - 1) % len(categories)]


def list_templates(db: Session, category_id: Optional[int] = None) -> List[HookTemplate]:
    """List hook templates; optionally filter by category."""
    q = db.query(HookTemplate).order_by(HookTemplate.sort_order, HookTemplate.name)
    if category_id is not None:
        q = q.filter(HookTemplate.category_id == category_id)
    return q.all()


def get_suggested_template_for_today(db: Session, organization_id: int | None = None) -> Optional[HookTemplate]:
    """Suggest a template for today using the workspace-aware category order."""
    category = get_rotated_category_for_today(db, organization_id)
    if category:
        templates = list_templates(db, category_id=category.id)
        if templates:
            today = datetime.now(timezone.utc)
            return templates[(today.timetuple().tm_yday - 1) % len(templates)]
    all_templates = list_templates(db)
    if all_templates:
        today = datetime.now(timezone.utc)
        return all_templates[(today.timetuple().tm_yday - 1) % len(all_templates)]
    return None


def render_template(template: HookTemplate, hook: str = "", body: str = "", cta: str = "") -> str:
    """Fill template placeholders. Uses defaults from template if not provided."""
    h = hook or template.default_hook or ""
    b = body or ""
    c = cta or template.default_cta or ""
    return template.body_template.replace("{hook}", h).replace("{body}", b).replace("{cta}", c)


SHARE_PSYCHOLOGY_TIPS = [
    {"id": "emotion", "title": "Emotion", "tip": "Emotional hooks tend to get more engagement; use sparingly and authentically."},
    {"id": "utility", "title": "Utility", "tip": "Clear, actionable tips and how-tos are often shared for later use."},
    {"id": "clarity", "title": "Clarity", "tip": "Short sentences and one main idea per post improve readability and shares."},
    {"id": "timing", "title": "Timing", "tip": "Match content tone to the business moment and audience need."},
    {"id": "cta", "title": "Call to action", "tip": "A simple, truthful CTA can encourage comments or qualified inquiries."},
]


def get_share_psychology_tips() -> list:
    return [dict(tip) for tip in SHARE_PSYCHOLOGY_TIPS]
