"""Add relational workspace evidence and package evidence links.

Revision ID: fg6b7c8d9e0f
Revises: ff5a6b7c8d9e
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "fg6b7c8d9e0f"
down_revision: Union[str, None] = "ff5a6b7c8d9e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workspace_claims",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(length=50), nullable=False, server_default="approved_fact"),
        sa.Column("review_status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_workspace_claims_organization_id", "workspace_claims", ["organization_id"])
    op.create_table(
        "workspace_claim_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("claim_id", sa.Integer(), sa.ForeignKey("workspace_claims.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("workspace_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("claim_id", "source_id", name="uq_workspace_claim_source"),
    )
    op.create_index("ix_workspace_claim_sources_claim_id", "workspace_claim_sources", ["claim_id"])
    op.create_index("ix_workspace_claim_sources_source_id", "workspace_claim_sources", ["source_id"])
    op.create_table(
        "content_package_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("content_package_id", sa.Integer(), sa.ForeignKey("content_packages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("workspace_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("claim_id", sa.Integer(), sa.ForeignKey("workspace_claims.id", ondelete="SET NULL"), nullable=True),
        sa.Column("evidence_type", sa.String(length=40), nullable=False, server_default="grounding"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_content_package_evidence_content_package_id", "content_package_evidence", ["content_package_id"])
    op.create_index("ix_content_package_evidence_source_id", "content_package_evidence", ["source_id"])
    op.create_index("ix_content_package_evidence_claim_id", "content_package_evidence", ["claim_id"])
    op.add_column("content_packages", sa.Column("source_ref_ids_json", sa.Text(), nullable=True))
    op.add_column("content_packages", sa.Column("claim_ref_ids_json", sa.Text(), nullable=True))
    op.add_column("content_packages", sa.Column("evidence_status", sa.String(length=30), nullable=False, server_default="unverified"))


def downgrade() -> None:
    op.drop_column("content_packages", "evidence_status")
    op.drop_column("content_packages", "claim_ref_ids_json")
    op.drop_column("content_packages", "source_ref_ids_json")
    op.drop_index("ix_content_package_evidence_claim_id", table_name="content_package_evidence")
    op.drop_index("ix_content_package_evidence_source_id", table_name="content_package_evidence")
    op.drop_index("ix_content_package_evidence_content_package_id", table_name="content_package_evidence")
    op.drop_table("content_package_evidence")
    op.drop_index("ix_workspace_claim_sources_source_id", table_name="workspace_claim_sources")
    op.drop_index("ix_workspace_claim_sources_claim_id", table_name="workspace_claim_sources")
    op.drop_table("workspace_claim_sources")
    op.drop_index("ix_workspace_claims_organization_id", table_name="workspace_claims")
    op.drop_table("workspace_claims")
