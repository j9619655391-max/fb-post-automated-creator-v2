"""Add reviewable pamphlet and print brief foundations.

Revision ID: fj9e0f1a2b3c
Revises: fi8d9e0f1a2b
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "fj9e0f1a2b3c"
down_revision: Union[str, None] = "fi8d9e0f1a2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pamphlet_briefs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("objective", sa.String(length=120), nullable=True),
        sa.Column("audience", sa.String(length=500), nullable=True),
        sa.Column("panel_count", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("paper_size", sa.String(length=40), nullable=False, server_default="A4"),
        sa.Column("orientation", sa.String(length=20), nullable=False, server_default="landscape"),
        sa.Column("fold_style", sa.String(length=40), nullable=False, server_default="half-fold"),
        sa.Column("trim_width_mm", sa.Integer(), nullable=False, server_default="297"),
        sa.Column("trim_height_mm", sa.Integer(), nullable=False, server_default="210"),
        sa.Column("bleed_mm", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("safe_area_mm", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("qr_url", sa.String(length=2048), nullable=True),
        sa.Column("accessibility_text", sa.Text(), nullable=True),
        sa.Column("content_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="draft"),
        sa.Column("approval_required", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_pamphlet_briefs_id", "pamphlet_briefs", ["id"], unique=False)
    op.create_index("ix_pamphlet_briefs_organization_id", "pamphlet_briefs", ["organization_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_pamphlet_briefs_organization_id", table_name="pamphlet_briefs")
    op.drop_index("ix_pamphlet_briefs_id", table_name="pamphlet_briefs")
    op.drop_table("pamphlet_briefs")
