"""add brand themes

Revision ID: f8c9d0e1f2a3
Revises: f7b8c9d0e1f2
"""

from alembic import op
import sqlalchemy as sa


revision = "f8c9d0e1f2a3"
down_revision = "f7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "brand_themes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("visual_style", sa.Text(), nullable=True),
        sa.Column("color_palette_json", sa.Text(), nullable=True),
        sa.Column("typography_json", sa.Text(), nullable=True),
        sa.Column("logo_position", sa.String(length=50), nullable=False, server_default="bottom_right"),
        sa.Column("background_style", sa.String(length=100), nullable=True),
        sa.Column("supported_formats_json", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "slug", name="uq_brand_themes_org_slug"),
    )
    op.create_index("ix_brand_themes_id", "brand_themes", ["id"])
    op.create_index("ix_brand_themes_organization_id", "brand_themes", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_brand_themes_organization_id", table_name="brand_themes")
    op.drop_index("ix_brand_themes_id", table_name="brand_themes")
    op.drop_table("brand_themes")
