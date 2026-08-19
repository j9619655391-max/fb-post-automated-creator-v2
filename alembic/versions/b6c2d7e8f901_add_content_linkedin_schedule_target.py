"""add content linkedin schedule target

Revision ID: b6c2d7e8f901
Revises: e6a396f1c707
Create Date: 2026-08-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b6c2d7e8f901"
down_revision: Union[str, Sequence[str], None] = "e6a396f1c707"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


platform_enum = sa.Enum(
    "FACEBOOK",
    "INSTAGRAM",
    "LINKEDIN",
    name="scheduledplatform",
)


def upgrade() -> None:
    """Add provider-neutral approval-time scheduling fields to content."""
    with op.batch_alter_table("content", schema=None) as batch_op:
        batch_op.add_column(sa.Column("schedule_platform", platform_enum, nullable=True))
        batch_op.add_column(sa.Column("schedule_linkedin_account_id", sa.Integer(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_content_schedule_linkedin_account_id"),
            ["schedule_linkedin_account_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_content_schedule_linkedin_account_id",
            "linkedin_accounts",
            ["schedule_linkedin_account_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    """Remove provider-neutral approval-time scheduling fields from content."""
    with op.batch_alter_table("content", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_content_schedule_linkedin_account_id",
            type_="foreignkey",
        )
        batch_op.drop_index(batch_op.f("ix_content_schedule_linkedin_account_id"))
        batch_op.drop_column("schedule_linkedin_account_id")
        batch_op.drop_column("schedule_platform")
