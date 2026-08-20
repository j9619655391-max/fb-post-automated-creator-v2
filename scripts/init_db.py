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
    """Create default categories/templates independently of user seeding."""
    if db.query(ContentCategory).first() is not None:
        return

    cat_motivation = ContentCategory(name="Motivation", slug="motivation", sort_order=1)
    cat_tips = ContentCategory(name="Tips", slug="tips", sort_order=2)
    cat_reflection = ContentCategory(name="Reflection", slug="reflection", sort_order=3)
    db.add_all([cat_motivation, cat_tips, cat_reflection])
    db.flush()
    db.add_all([
        HookTemplate(
            name="Hook + Body + CTA",
            body_template="{hook}\n\n{body}\n\n{cta}",
            default_hook="Here's something to think about.",
            default_cta="What would you add?",
            category_id=cat_motivation.id,
            sort_order=1,
        ),
        HookTemplate(
            name="Question hook",
            body_template="{hook}\n\n{body}\n\n{cta}",
            default_hook="Did you know?",
            default_cta="Share if this helped.",
            category_id=cat_tips.id,
            sort_order=2,
        ),
    ])


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
