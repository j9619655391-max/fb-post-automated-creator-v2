"""normalize opportunity migration chain

Revision ID: fa0e1f2a3b4c
Revises: f9d0e1f2a3b4

This follow-up revision intentionally performs no schema operation. The table
is created by f9d0e1f2a3b4; keeping this revision preserves the already-created
local migration chain without duplicating the table creation.
"""

revision = "fa0e1f2a3b4c"
down_revision = "f9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
