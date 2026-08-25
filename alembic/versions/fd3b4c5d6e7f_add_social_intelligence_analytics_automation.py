"""add social intelligence, analytics, and automation controls

Revision ID: fd3b4c5d6e7f
Revises: fc2a3b4c5d6e
"""

from alembic import op
import sqlalchemy as sa


revision = "fd3b4c5d6e7f"
down_revision = "fc2a3b4c5d6e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workspace_profiles", sa.Column("watch_terms_json", sa.Text(), nullable=True))
    op.add_column("workspace_profiles", sa.Column("competitor_urls_json", sa.Text(), nullable=True))
    op.add_column("content", sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("content", sa.Column("risk_tier", sa.String(length=20), nullable=False, server_default="low"))
    op.add_column("content", sa.Column("risk_flags_json", sa.Text(), nullable=True))
    op.create_index("ix_content_risk_score", "content", ["risk_score"])
    op.create_index("ix_content_risk_tier", "content", ["risk_tier"])

    op.create_table(
        "social_signals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("signal_type", sa.String(length=40), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("source_url", sa.String(length=2000), nullable=True),
        sa.Column("external_id", sa.String(length=1000), nullable=False),
        sa.Column("query", sa.String(length=500), nullable=True),
        sa.Column("subject", sa.String(length=500), nullable=True),
        sa.Column("title", sa.String(length=1000), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("publisher", sa.String(length=500), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sentiment", sa.String(length=20), nullable=False, server_default="neutral"),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("engagement_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="new"),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "source_type", "external_id", name="uq_social_signals_org_source_external"),
    )
    for name, column in (
        ("ix_social_signals_id", "id"),
        ("ix_social_signals_organization_id", "organization_id"),
        ("ix_social_signals_signal_type", "signal_type"),
        ("ix_social_signals_source_type", "source_type"),
        ("ix_social_signals_published_at", "published_at"),
        ("ix_social_signals_status", "status"),
    ):
        op.create_index(name, "social_signals", [column])

    op.create_table(
        "publishing_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.Column("publish_status_id", sa.Integer(), nullable=True),
        sa.Column("platform", sa.String(length=30), nullable=False),
        sa.Column("platform_post_id", sa.String(length=500), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reach", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("engagements", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reactions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comments", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shares", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("video_views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("saves", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("negative_feedback", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("engagement_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source", sa.String(length=40), nullable=False, server_default="manual"),
        sa.Column("raw_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["publish_status_id"], ["content_publish_status.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("publish_status_id", "captured_at", name="uq_publishing_metrics_status_captured"),
    )
    for name, column in (
        ("ix_publishing_metrics_id", "id"),
        ("ix_publishing_metrics_organization_id", "organization_id"),
        ("ix_publishing_metrics_content_id", "content_id"),
        ("ix_publishing_metrics_publish_status_id", "publish_status_id"),
        ("ix_publishing_metrics_platform", "platform"),
        ("ix_publishing_metrics_platform_post_id", "platform_post_id"),
        ("ix_publishing_metrics_captured_at", "captured_at"),
    ):
        op.create_index(name, "publishing_metrics", [column])

    op.create_table(
        "workspace_automation_policies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("approval_mode", sa.String(length=30), nullable=False, server_default="required"),
        sa.Column("autopilot_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("emergency_stop", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("emergency_stop_reason", sa.Text(), nullable=True),
        sa.Column("max_autopilot_risk_tier", sa.String(length=20), nullable=False, server_default="low"),
        sa.Column("max_autopilot_posts_per_day", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_approval_batch_size", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("approval_batch_window_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_daily_generated_drafts", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("organization_id", name="uq_workspace_automation_policies_org"),
    )
    op.create_index("ix_workspace_automation_policies_id", "workspace_automation_policies", ["id"])
    op.create_index("ix_workspace_automation_policies_organization_id", "workspace_automation_policies", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_workspace_automation_policies_organization_id", table_name="workspace_automation_policies")
    op.drop_index("ix_workspace_automation_policies_id", table_name="workspace_automation_policies")
    op.drop_table("workspace_automation_policies")
    for name in (
        "ix_publishing_metrics_captured_at",
        "ix_publishing_metrics_platform_post_id",
        "ix_publishing_metrics_platform",
        "ix_publishing_metrics_publish_status_id",
        "ix_publishing_metrics_content_id",
        "ix_publishing_metrics_organization_id",
        "ix_publishing_metrics_id",
    ):
        op.drop_index(name, table_name="publishing_metrics")
    op.drop_table("publishing_metrics")
    for name in (
        "ix_social_signals_status",
        "ix_social_signals_published_at",
        "ix_social_signals_source_type",
        "ix_social_signals_signal_type",
        "ix_social_signals_organization_id",
        "ix_social_signals_id",
    ):
        op.drop_index(name, table_name="social_signals")
    op.drop_table("social_signals")
    op.drop_index("ix_content_risk_tier", table_name="content")
    op.drop_index("ix_content_risk_score", table_name="content")
    op.drop_column("content", "risk_flags_json")
    op.drop_column("content", "risk_tier")
    op.drop_column("content", "risk_score")
    op.drop_column("workspace_profiles", "competitor_urls_json")
    op.drop_column("workspace_profiles", "watch_terms_json")
