"""Workspace-level safety controls for approval and controlled automation."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class WorkspaceAutomationPolicy(Base):
    """One safety policy per workspace; conservative defaults are intentional."""

    __tablename__ = "workspace_automation_policies"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    approval_mode = Column(String(30), nullable=False, default="required")  # required or controlled
    autopilot_enabled = Column(Boolean, nullable=False, default=False)
    emergency_stop = Column(Boolean, nullable=False, default=False)
    emergency_stop_reason = Column(Text, nullable=True)
    max_autopilot_risk_tier = Column(String(20), nullable=False, default="low")
    max_autopilot_posts_per_day = Column(Integer, nullable=False, default=0)
    max_approval_batch_size = Column(Integer, nullable=False, default=1)
    approval_batch_window_minutes = Column(Integer, nullable=False, default=0)
    max_daily_generated_drafts = Column(Integer, nullable=False, default=20)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    organization = relationship("Organization", backref="automation_policy", uselist=False)
    updated_by = relationship("User")

    __table_args__ = (UniqueConstraint("organization_id", name="uq_workspace_automation_policies_org"),)
