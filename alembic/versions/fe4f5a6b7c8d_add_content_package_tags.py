"""add tags to content packages

Revision ID: fe4f5a6b7c8d
Revises: fd3b4c5d6e7f
"""

from alembic import op
import sqlalchemy as sa


revision = "fe4f5a6b7c8d"
down_revision = "fd3b4c5d6e7f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("content_packages", sa.Column("tags_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("content_packages", "tags_json")
