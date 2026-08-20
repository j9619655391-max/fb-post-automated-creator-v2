"""add workspace intelligence profile and sources

Revision ID: c3d4e5f6a7b8
Revises: b6c2d7e8f901
Create Date: 2026-08-21 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b6c2d7e8f901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workspace_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("business_description", sa.Text(), nullable=True),
        sa.Column("mission", sa.Text(), nullable=True),
        sa.Column("industry", sa.String(length=255), nullable=True),
        sa.Column("services_json", sa.Text(), nullable=True),
        sa.Column("products_json", sa.Text(), nullable=True),
        sa.Column("target_audience", sa.Text(), nullable=True),
        sa.Column("locations_json", sa.Text(), nullable=True),
        sa.Column("brand_voice", sa.Text(), nullable=True),
        sa.Column("tone", sa.String(length=100), nullable=True),
        sa.Column("keywords_json", sa.Text(), nullable=True),
        sa.Column("preferred_languages_json", sa.Text(), nullable=True),
        sa.Column("contact_email", sa.String(length=320), nullable=True),
        sa.Column("contact_phone", sa.String(length=80), nullable=True),
        sa.Column("whatsapp_display_phone", sa.String(length=80), nullable=True),
        sa.Column("whatsapp_business_account_id", sa.String(length=255), nullable=True),
        sa.Column("website_url", sa.String(length=2048), nullable=True),
        sa.Column("linkedin_url", sa.String(length=2048), nullable=True),
        sa.Column("facebook_url", sa.String(length=2048), nullable=True),
        sa.Column("instagram_url", sa.String(length=2048), nullable=True),
        sa.Column("whatsapp_url", sa.String(length=2048), nullable=True),
        sa.Column("approved_claims_json", sa.Text(), nullable=True),
        sa.Column("prohibited_claims_json", sa.Text(), nullable=True),
        sa.Column("last_refreshed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id"),
    )
    op.create_index("ix_workspace_profiles_id", "workspace_profiles", ["id"], unique=False)
    op.create_index("ix_workspace_profiles_organization_id", "workspace_profiles", ["organization_id"], unique=True)

    op.create_table(
        "workspace_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("trust_level", sa.String(length=50), nullable=False, server_default="user_supplied"),
        sa.Column("review_status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "source_type", "url", name="uq_workspace_source_org_type_url"),
    )
    op.create_index("ix_workspace_sources_id", "workspace_sources", ["id"], unique=False)
    op.create_index("ix_workspace_sources_organization_id", "workspace_sources", ["organization_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_workspace_sources_organization_id", table_name="workspace_sources")
    op.drop_index("ix_workspace_sources_id", table_name="workspace_sources")
    op.drop_table("workspace_sources")
    op.drop_index("ix_workspace_profiles_organization_id", table_name="workspace_profiles")
    op.drop_index("ix_workspace_profiles_id", table_name="workspace_profiles")
    op.drop_table("workspace_profiles")
