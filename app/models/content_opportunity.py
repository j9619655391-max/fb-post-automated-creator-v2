from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Float, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class OpportunityStatus:
    NEW = "new"
    REVIEWED = "reviewed"
    USED = "used"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class ContentOpportunity(Base):
    """Fresh, source-grounded content idea candidate for a workspace."""

    __tablename__ = "content_opportunities"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)
    source_url = Column(String(2048), nullable=True)
    publisher = Column(String(500), nullable=True)
    external_id = Column(String(500), nullable=True)
    title = Column(String(1000), nullable=False)
    summary = Column(Text, nullable=True)
    source_published_at = Column(DateTime(timezone=True), nullable=True)
    discovered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    freshness_score = Column(Float, nullable=False, default=0.0)
    relevance_score = Column(Float, nullable=False, default=0.0)
    trust_score = Column(Float, nullable=False, default=0.0)
    status = Column(String(30), nullable=False, default=OpportunityStatus.NEW, index=True)
    metadata_json = Column(Text, nullable=True)
    organization = relationship("Organization", backref="content_opportunities")

    __table_args__ = (
        UniqueConstraint("organization_id", "source_type", "external_id", name="uq_opportunities_org_source_external"),
    )
