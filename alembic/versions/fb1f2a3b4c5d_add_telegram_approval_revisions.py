"""add telegram approval and content revisions

Revision ID: fb1f2a3b4c5d
Revises: fa0e1f2a3b4c
"""

from alembic import op
import sqlalchemy as sa


revision = "fb1f2a3b4c5d"
down_revision = "fa0e1f2a3b4c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content_revisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=True),
        sa.Column("parent_content_id", sa.Integer(), nullable=False),
        sa.Column("revised_content_id", sa.Integer(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("feedback_note", sa.Text(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_content_id"], ["content.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["revised_content_id"], ["content.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("revised_content_id", name="uq_content_revisions_revised_content"),
    )
    op.create_index("ix_content_revisions_id", "content_revisions", ["id"])
    op.create_index("ix_content_revisions_organization_id", "content_revisions", ["organization_id"])
    op.create_index("ix_content_revisions_parent_content_id", "content_revisions", ["parent_content_id"])
    op.create_index("ix_content_revisions_revised_content_id", "content_revisions", ["revised_content_id"])

    op.create_table(
        "telegram_approval_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.String(length=255), nullable=False),
        sa.Column("approver_user_id", sa.String(length=255), nullable=True),
        sa.Column("telegram_message_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("rejection_note", sa.Text(), nullable=True),
        sa.Column("last_update_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_telegram_approval_requests_id", "telegram_approval_requests", ["id"])
    op.create_index("ix_telegram_approval_requests_organization_id", "telegram_approval_requests", ["organization_id"])
    op.create_index("ix_telegram_approval_requests_content_id", "telegram_approval_requests", ["content_id"])
    op.create_index("ix_telegram_approval_requests_status", "telegram_approval_requests", ["status"])


def downgrade() -> None:
    op.drop_index("ix_telegram_approval_requests_status", table_name="telegram_approval_requests")
    op.drop_index("ix_telegram_approval_requests_content_id", table_name="telegram_approval_requests")
    op.drop_index("ix_telegram_approval_requests_organization_id", table_name="telegram_approval_requests")
    op.drop_index("ix_telegram_approval_requests_id", table_name="telegram_approval_requests")
    op.drop_table("telegram_approval_requests")
    op.drop_index("ix_content_revisions_revised_content_id", table_name="content_revisions")
    op.drop_index("ix_content_revisions_parent_content_id", table_name="content_revisions")
    op.drop_index("ix_content_revisions_organization_id", table_name="content_revisions")
    op.drop_index("ix_content_revisions_id", table_name="content_revisions")
    op.drop_table("content_revisions")
