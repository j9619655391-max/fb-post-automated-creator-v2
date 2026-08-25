"""Bootstrap the local Hinglish quote-page workspace without affecting other organizations."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.models  # noqa: F401
from app.core.database import SessionLocal
from app.models.organization import Organization
from app.models.workspace_intelligence import WorkspaceProfile
from scripts.init_db import _seed_categories

ORG_SLUG = "love-truth-motivational-pain-quotes"


def bootstrap() -> int:
    db = SessionLocal()
    try:
        _seed_categories(db)
        organization = db.query(Organization).filter(Organization.slug == ORG_SLUG).first()
        if not organization:
            raise SystemExit(f"Workspace not found: {ORG_SLUG}")
        profile = db.query(WorkspaceProfile).filter(WorkspaceProfile.organization_id == organization.id).first()
        if profile is None:
            profile = WorkspaceProfile(organization_id=organization.id)
            db.add(profile)
        profile.business_description = "A social media quote page sharing Love, Truth, Motivational, and Pain quotes in natural Hinglish using Roman Hindi and English."
        profile.mission = "Make relatable emotions and life lessons easy to feel and share."
        profile.tagline = "Dil ki baat, Hinglish alfaaz mein."
        profile.industry = "Hinglish quotes and digital content"
        profile.services_json = json.dumps(["Hinglish quote content", "Branded social media image posts"])
        profile.products_json = json.dumps(["Love quotes", "Truth quotes", "Motivational quotes", "Pain quotes"])
        profile.target_audience = "People who connect with relatable love, reality, motivation, healing, and pain content."
        profile.brand_voice = "Emotional, relatable, concise, poetic, honest, and never preachy."
        profile.tone = "Warm, heartfelt, reflective, hopeful, and authentic."
        profile.visual_style = "Image-led quote cards with expressive photography or gradients, strong text-safe areas, bold hierarchy, and a consistent branded footer."
        profile.brand_colors_json = json.dumps(["#111827", "#F59E0B", "#F8FAFC", "#EC4899"])
        profile.font_preferences_json = json.dumps(["DejaVu Sans", "DejaVu Serif"])
        profile.preferred_content_formats_json = json.dumps(["branded quote image", "square social card", "carousel quote story"])
        profile.keywords_json = json.dumps(["love", "truth", "motivation", "pain", "healing", "dard", "pyaar", "sach", "zindagi"])
        profile.preferred_languages_json = json.dumps(["Hinglish", "Roman Hindi", "English"])
        profile.approval_required = True
        db.commit()
        print(f"Bootstrapped {organization.name} (id={organization.id}) with Hinglish quote profile and categories.")
        return organization.id
    finally:
        db.close()


if __name__ == "__main__":
    bootstrap()
