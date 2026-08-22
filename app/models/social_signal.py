"""Persisted public social-listening and audience-intelligence signals."""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SocialSignal(Base):
    """A public, provenance-linked signal used for content intelligence."""

    __tablename__ = "social_signals"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    signal_type = Column(String(40), nullable=False, index=True)  # mention, competitor, audience, trend
    source_type = Column(String(40), nullable=False, index=True)  # rss, news, research, manual, provider
    source_url = Column(String(2000), nullable=True)
    external_id = Column(String(1000), nullable=False)
    query = Column(String(500), nullable=True)
    subject = Column(String(500), nullable=True)
    title = Column(String(1000), nullable=False)
    excerpt = Column(Text, nullable=True)
    publisher = Column(String(500), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    sentiment = Column(String(20), nullable=False, default="neutral")
    sentiment_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=False, default=0.0)
    engagement_count = Column(Integer, nullable=False, default=0)
    status = Column(String(30), nullable=False, default="new", index=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    organization = relationship("Organization", backref="social_signals")

    __table_args__ = (
        UniqueConstraint("organization_id", "source_type", "external_id", name="uq_social_signals_org_source_external"),
    )
