"""add content packages

Revision ID: fc2a3b4c5d6e
Revises: fb1f2a3b4c5d
"""

from alembic import op
import sqlalchemy as sa


revision = "fc2a3b4c5d6e"
down_revision = "fb1f2a3b4c5d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content_packages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("source_content_id", sa.Integer(), nullable=False),
        sa.Column("theme_id", sa.Integer(), nullable=True),
        sa.Column("opportunity_id", sa.Integer(), nullable=True),
        sa.Column("platform", sa.String(length=30), nullable=False),
        sa.Column("headline", sa.String(length=1000), nullable=True),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("cta", sa.String(length=1000), nullable=True),
        sa.Column("hashtags_json", sa.Text(), nullable=True),
        sa.Column("source_urls_json", sa.Text(), nullable=True),
        sa.Column("media_variant_ids_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_content_id"], ["content.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["theme_id"], ["brand_themes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["opportunity_id"], ["content_opportunities.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("source_content_id", "platform", name="uq_content_packages_source_platform"),
    )
    op.create_index("ix_content_packages_id", "content_packages", ["id"])
    op.create_index("ix_content_packages_organization_id", "content_packages", ["organization_id"])
    op.create_index("ix_content_packages_source_content_id", "content_packages", ["source_content_id"])
    op.create_index("ix_content_packages_theme_id", "content_packages", ["theme_id"])
    op.create_index("ix_content_packages_opportunity_id", "content_packages", ["opportunity_id"])


def downgrade() -> None:
    op.drop_index("ix_content_packages_opportunity_id", table_name="content_packages")
    op.drop_index("ix_content_packages_theme_id", table_name="content_packages")
    op.drop_index("ix_content_packages_source_content_id", table_name="content_packages")
    op.drop_index("ix_content_packages_organization_id", table_name="content_packages")
    op.drop_index("ix_content_packages_id", table_name="content_packages")
    op.drop_table("content_packages")
