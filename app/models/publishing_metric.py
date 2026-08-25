"""Publishing performance snapshots captured from provider analytics."""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class PublishingMetric(Base):
    """Immutable-ish point-in-time metrics for a published target."""

    __tablename__ = "publishing_metrics"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    content_id = Column(Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False, index=True)
    publish_status_id = Column(Integer, ForeignKey("content_publish_status.id", ondelete="SET NULL"), nullable=True, index=True)
    platform = Column(String(30), nullable=False, index=True)
    platform_post_id = Column(String(500), nullable=True, index=True)
    captured_at = Column(DateTime(timezone=True), nullable=False, index=True)
    impressions = Column(Integer, nullable=False, default=0)
    reach = Column(Integer, nullable=False, default=0)
    engagements = Column(Integer, nullable=False, default=0)
    reactions = Column(Integer, nullable=False, default=0)
    comments = Column(Integer, nullable=False, default=0)
    shares = Column(Integer, nullable=False, default=0)
    clicks = Column(Integer, nullable=False, default=0)
    video_views = Column(Integer, nullable=False, default=0)
    saves = Column(Integer, nullable=False, default=0)
    negative_feedback = Column(Integer, nullable=False, default=0)
    engagement_rate = Column(Float, nullable=False, default=0.0)
    source = Column(String(40), nullable=False, default="manual")
    raw_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    organization = relationship("Organization", backref="publishing_metrics")
    content = relationship("Content", backref="publishing_metrics")
    publish_status = relationship("ContentPublishStatus", backref="publishing_metrics")

    __table_args__ = (
        UniqueConstraint("publish_status_id", "captured_at", name="uq_publishing_metrics_status_captured"),
    )
