"""Remove redundant workspace profile organization index.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-21 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(
        "ix_workspace_profiles_organization_id",
        table_name="workspace_profiles",
    )


def downgrade() -> None:
    op.create_index(
        "ix_workspace_profiles_organization_id",
        "workspace_profiles",
        ["organization_id"],
        unique=True,
    )
