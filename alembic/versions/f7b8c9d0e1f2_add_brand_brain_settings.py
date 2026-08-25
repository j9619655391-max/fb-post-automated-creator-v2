"""add brand brain settings

Revision ID: f7b8c9d0e1f2
Revises: f6a7b8c9d0e1
"""

from alembic import op
import sqlalchemy as sa


revision = "f7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workspace_profiles", sa.Column("tagline", sa.String(length=500), nullable=True))
    op.add_column("workspace_profiles", sa.Column("visual_style", sa.Text(), nullable=True))
    op.add_column("workspace_profiles", sa.Column("brand_colors_json", sa.Text(), nullable=True))
    op.add_column("workspace_profiles", sa.Column("font_preferences_json", sa.Text(), nullable=True))
    op.add_column("workspace_profiles", sa.Column("preferred_content_formats_json", sa.Text(), nullable=True))
    op.add_column("workspace_profiles", sa.Column("content_cadence_json", sa.Text(), nullable=True))
    op.add_column(
        "workspace_profiles",
        sa.Column("logo_media_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_workspace_profiles_logo_media_id",
        "workspace_profiles",
        ["logo_media_id"],
    )
    op.create_foreign_key(
        "fk_workspace_profiles_logo_media_id_media",
        "workspace_profiles",
        "media",
        ["logo_media_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column(
        "workspace_profiles",
        sa.Column("telegram_approval_chat_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "workspace_profiles",
        sa.Column("telegram_approval_user_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "workspace_profiles",
        sa.Column(
            "telegram_approval_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "workspace_profiles",
        sa.Column(
            "approval_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("workspace_profiles", "approval_required")
    op.drop_column("workspace_profiles", "telegram_approval_enabled")
    op.drop_column("workspace_profiles", "telegram_approval_user_id")
    op.drop_column("workspace_profiles", "telegram_approval_chat_id")
    op.drop_constraint(
        "fk_workspace_profiles_logo_media_id_media",
        "workspace_profiles",
        type_="foreignkey",
    )
    op.drop_index("ix_workspace_profiles_logo_media_id", table_name="workspace_profiles")
    op.drop_column("workspace_profiles", "logo_media_id")
    op.drop_column("workspace_profiles", "content_cadence_json")
    op.drop_column("workspace_profiles", "preferred_content_formats_json")
    op.drop_column("workspace_profiles", "font_preferences_json")
    op.drop_column("workspace_profiles", "brand_colors_json")
    op.drop_column("workspace_profiles", "visual_style")
    op.drop_column("workspace_profiles", "tagline")
