"""add content opportunities

Revision ID: f9d0e1f2a3b4
Revises: f8c9d0e1f2a3
"""

from alembic import op
import sqlalchemy as sa


revision = "f9d0e1f2a3b4"
down_revision = "f8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content_opportunities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("publisher", sa.String(length=500), nullable=True),
        sa.Column("external_id", sa.String(length=500), nullable=True),
        sa.Column("title", sa.String(length=1000), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("source_published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discovered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("freshness_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("relevance_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("trust_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="new"),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "source_type", "external_id", name="uq_opportunities_org_source_external"),
    )
    op.create_index("ix_content_opportunities_id", "content_opportunities", ["id"])
    op.create_index("ix_content_opportunities_organization_id", "content_opportunities", ["organization_id"])
    op.create_index("ix_content_opportunities_status", "content_opportunities", ["status"])


def downgrade() -> None:
    op.drop_index("ix_content_opportunities_status", table_name="content_opportunities")
    op.drop_index("ix_content_opportunities_organization_id", table_name="content_opportunities")
    op.drop_index("ix_content_opportunities_id", table_name="content_opportunities")
    op.drop_table("content_opportunities")
