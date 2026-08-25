"""Add indexes declared by workspace evidence models.

Revision ID: fh7c8d9e0f1a
Revises: fg6b7c8d9e0f
"""
from typing import Sequence, Union

from alembic import op


revision: str = "fh7c8d9e0f1a"
down_revision: Union[str, None] = "fg6b7c8d9e0f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_workspace_claims_id", "workspace_claims", ["id"], unique=False)
    op.create_index("ix_workspace_claim_sources_id", "workspace_claim_sources", ["id"], unique=False)
    op.create_index("ix_content_package_evidence_id", "content_package_evidence", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_content_package_evidence_id", table_name="content_package_evidence")
    op.drop_index("ix_workspace_claim_sources_id", table_name="workspace_claim_sources")
    op.drop_index("ix_workspace_claims_id", table_name="workspace_claims")
