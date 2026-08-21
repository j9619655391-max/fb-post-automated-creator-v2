"""add provider account metadata

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-21 14:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("meta_pages", sa.Column("instagram_business_account_id", sa.String(length=64), nullable=True))
    op.create_index(
        "ix_meta_pages_instagram_business_account_id",
        "meta_pages",
        ["instagram_business_account_id"],
        unique=False,
    )
    op.add_column("linkedin_accounts", sa.Column("organization_role", sa.String(length=64), nullable=True))
    op.add_column("linkedin_accounts", sa.Column("organization_role_state", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("linkedin_accounts", "organization_role_state")
    op.drop_column("linkedin_accounts", "organization_role")
    op.drop_index("ix_meta_pages_instagram_business_account_id", table_name="meta_pages")
    op.drop_column("meta_pages", "instagram_business_account_id")
