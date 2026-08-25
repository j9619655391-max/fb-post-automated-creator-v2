"""Add media asset provenance metadata.

Revision ID: fi8d9e0f1a2b
Revises: fh7c8d9e0f1a
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "fi8d9e0f1a2b"
down_revision: Union[str, None] = "fh7c8d9e0f1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("media", sa.Column("source_kind", sa.String(length=40), nullable=False, server_default="uploaded"))
    op.add_column("media", sa.Column("source_url", sa.String(length=2048), nullable=True))
    op.add_column("media", sa.Column("license_info", sa.Text(), nullable=True))
    op.add_column("media", sa.Column("attribution", sa.Text(), nullable=True))
    op.add_column("media", sa.Column("provenance_status", sa.String(length=30), nullable=False, server_default="unverified"))


def downgrade() -> None:
    op.drop_column("media", "provenance_status")
    op.drop_column("media", "attribution")
    op.drop_column("media", "license_info")
    op.drop_column("media", "source_url")
    op.drop_column("media", "source_kind")
