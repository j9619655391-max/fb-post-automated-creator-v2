"""Apply migrations and optionally seed safe local development data."""
import os
import subprocess
import sys
from pathlib import Path

import app.models  # noqa: F401 - register all models for SQLAlchemy/Alembic
from app.core.database import SessionLocal
from app.models.content import Content, ContentStatus
from app.models.content_category import ContentCategory
from app.models.hook_template import HookTemplate
from app.models.user import User

ROOT = Path(__file__).resolve().parents[1]


def run_migrations() -> None:
    """Apply versioned schema migrations before touching application data."""
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=ROOT,
        check=True,
    )


def _seed_categories(db) -> None:
    """Create missing business-aware categories/templates without deleting existing data."""
    definitions = [
        ("Product Showcase", "product-showcase", 1),
        ("Collection Launch", "collection-launch", 2),
        ("Bridal & Occasion", "bridal-occasion", 3),
        ("Styling Tips", "styling-tips", 4),
        ("Fabric & Craft", "fabric-craft", 5),
        ("Behind the Scenes", "behind-the-scenes", 6),
        ("Customer Story", "customer-story", 7),
        ("Offer & Booking", "offer-booking", 8),
        ("Fashion Quote", "fashion-quote", 9),
        ("Seasonal / Festival", "seasonal-festival", 10),
        ("Service Showcase", "service-showcase", 20),
        ("Case Study & Results", "case-study-results", 21),
        ("Educational / How-to", "educational-howto", 22),
        ("Industry Insights", "industry-insights", 23),
        ("Client Story", "client-story", 24),
        ("Company & Team", "company-culture", 25),
        ("Motivation", "motivation", 90),
        ("Tips", "tips", 91),
        ("Reflection", "reflection", 92),
    ]
    categories: dict[str, ContentCategory] = {}
    for name, slug, sort_order in definitions:
        category = db.query(ContentCategory).filter(ContentCategory.slug == slug).first()
        if category is None:
            category = ContentCategory(name=name, slug=slug, sort_order=sort_order)
            db.add(category)
            db.flush()
        categories[slug] = category

    existing_hooks = {row.name for row in db.query(HookTemplate).all()}
    hook_definitions = [
        ("Fashion product showcase", "{hook}\\n\\n{body}\\n\\n{cta}", "Meet the detail that makes this piece special.", "Message us for measurements and availability.", "product-showcase"),
        ("Collection launch", "{hook}\\n\\n{body}\\n\\n{cta}", "A new look has arrived.", "Book a consultation to explore the collection.", "collection-launch"),
        ("Styling tip", "{hook}\\n\\n{body}\\n\\n{cta}", "Style note:", "Save this idea and ask us for a custom recommendation.", "styling-tips"),
        ("Fashion quote", "{hook}\\n\\n{body}\\n\\n{cta}", "A thought for your wardrobe:", "Follow for more fashion inspiration.", "fashion-quote"),
        ("Hook + Body + CTA", "{hook}\\n\\n{body}\\n\\n{cta}", "Here's something to think about.", "What would you add?", "motivation"),
        ("Question hook", "{hook}\\n\\n{body}\\n\\n{cta}", "Did you know?", "Share if this helped.", "tips"),
        ("Service showcase", "{hook}\\n\\n{body}\\n\\n{cta}", "A practical solution for your next business goal:", "Talk to us about your requirements.", "service-showcase"),
        ("Case study result", "{hook}\\n\\n{body}\\n\\n{cta}", "What changed for this client:", "Ask us how we can help.", "case-study-results"),
        ("Educational how-to", "{hook}\\n\\n{body}\\n\\n{cta}", "A useful idea for your work:", "Save this for later.", "educational-howto"),
        ("Industry insight", "{hook}\\n\\n{body}\\n\\n{cta}", "What this means for businesses today:", "Share your perspective.", "industry-insights"),
        ("Client story", "{hook}\\n\\n{body}\\n\\n{cta}", "A client perspective:", "Message us to discuss your goal.", "client-story"),
        ("Company culture", "{hook}\\n\\n{body}\\n\\n{cta}", "Behind the work:", "Meet the team behind the solution.", "company-culture"),
    ]
    for name, body_template, default_hook, default_cta, slug in hook_definitions:
        if name in existing_hooks:
            continue
        db.add(HookTemplate(
            name=name,
            body_template=body_template,
            default_hook=default_hook,
            default_cta=default_cta,
            category_id=categories[slug].id,
            sort_order=categories[slug].sort_order,
        ))


def create_sample_data() -> None:
    """Create optional sample users/content and always seed missing defaults."""
    db = SessionLocal()
    try:
        seed_sample_data = os.getenv("SEED_SAMPLE_DATA", "false").lower() in {"1", "true", "yes", "on"}
        users_created = False
        if seed_sample_data and db.query(User).first() is None:
            from app.core import security

            admin = User(
                username="admin",
                email="admin@example.com",
                full_name="Admin User",
                hashed_password=security.get_password_hash("admin123"),
                is_active=True,
                is_admin=True,
            )
            user = User(
                username="user1",
                email="user1@example.com",
                full_name="Regular User",
                hashed_password=security.get_password_hash("password123"),
                is_active=True,
                is_admin=False,
            )
            db.add_all([admin, user])
            db.flush()
            users_created = True

            db.add_all([
                Content(
                    title="Sample Draft Content",
                    body="This is a sample draft content.",
                    status=ContentStatus.DRAFT,
                    created_by_id=user.id,
                ),
                Content(
                    title="Sample Pending Content",
                    body="This content is pending approval.",
                    status=ContentStatus.PENDING_APPROVAL,
                    created_by_id=user.id,
                ),
            ])

        before_categories = db.query(ContentCategory).count()
        _seed_categories(db)
        db.commit()
        if users_created:
            print("Sample users/content created.")
        if before_categories == 0:
            print("Default content categories/templates created.")
        else:
            print("Default content categories already present.")
    except Exception as exc:
        db.rollback()
        raise RuntimeError(f"Error creating local seed data: {exc}") from exc
    finally:
        db.close()


if __name__ == "__main__":
    run_migrations()
    create_sample_data()
