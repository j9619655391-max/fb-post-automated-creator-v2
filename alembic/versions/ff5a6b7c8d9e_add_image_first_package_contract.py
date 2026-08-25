"""Add durable image-first package contract fields.

Revision ID: ff5a6b7c8d9e
Revises: fe4f5a6b7c8d
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ff5a6b7c8d9e"
down_revision: Union[str, None] = "fe4f5a6b7c8d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("content_packages", sa.Column("image_text", sa.Text(), nullable=True))
    op.add_column("content_packages", sa.Column("alt_text", sa.Text(), nullable=True))
    op.add_column("content_packages", sa.Column("objective", sa.String(length=120), nullable=True))
    op.add_column("content_packages", sa.Column("creative_archetype", sa.String(length=120), nullable=True))
    op.add_column("content_packages", sa.Column("source_refs_json", sa.Text(), nullable=True))
    op.add_column("content_packages", sa.Column("claim_refs_json", sa.Text(), nullable=True))
    op.add_column("content_packages", sa.Column("visual_brief_json", sa.Text(), nullable=True))
    op.add_column("content_packages", sa.Column("asset_provenance_json", sa.Text(), nullable=True))
    op.add_column("content_packages", sa.Column("visual_qa_status", sa.String(length=30), nullable=False, server_default="not_run"))
    op.add_column("content_packages", sa.Column("visual_qa_flags_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("content_packages", "visual_qa_flags_json")
    op.drop_column("content_packages", "visual_qa_status")
    op.drop_column("content_packages", "asset_provenance_json")
    op.drop_column("content_packages", "visual_brief_json")
    op.drop_column("content_packages", "claim_refs_json")
    op.drop_column("content_packages", "source_refs_json")
    op.drop_column("content_packages", "creative_archetype")
    op.drop_column("content_packages", "objective")
    op.drop_column("content_packages", "alt_text")
    op.drop_column("content_packages", "image_text")
