"""add generation plan observability

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-21 13:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("content_generation_plans", sa.Column("last_provider", sa.String(length=100), nullable=True))
    op.add_column("content_generation_plans", sa.Column("last_error_code", sa.String(length=100), nullable=True))
    op.add_column("content_generation_plans", sa.Column("last_error_message", sa.Text(), nullable=True))
    op.add_column(
        "content_generation_plans",
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("content_generation_plans", sa.Column("last_retry_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("content_generation_plans", "last_retry_at")
    op.drop_column("content_generation_plans", "failure_count")
    op.drop_column("content_generation_plans", "last_error_message")
    op.drop_column("content_generation_plans", "last_error_code")
    op.drop_column("content_generation_plans", "last_provider")
