from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ContentPackage(Base):
    __tablename__ = "content_packages"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    source_content_id = Column(Integer, ForeignKey("content.id", ondelete="CASCADE"), nullable=False, index=True)
    theme_id = Column(Integer, ForeignKey("brand_themes.id", ondelete="SET NULL"), nullable=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("content_opportunities.id", ondelete="SET NULL"), nullable=True, index=True)
    platform = Column(String(30), nullable=False)
    headline = Column(String(1000), nullable=True)
    # Image copy is intentionally separate from the full platform caption.
    image_text = Column(Text, nullable=True)
    caption = Column(Text, nullable=False)
    alt_text = Column(Text, nullable=True)
    cta = Column(String(1000), nullable=True)
    objective = Column(String(120), nullable=True)
    creative_archetype = Column(String(120), nullable=True)
    hashtags_json = Column(Text, nullable=True)
    tags_json = Column(Text, nullable=True)
    source_urls_json = Column(Text, nullable=True)
    source_refs_json = Column(Text, nullable=True)
    claim_refs_json = Column(Text, nullable=True)
    source_ref_ids_json = Column(Text, nullable=True)
    claim_ref_ids_json = Column(Text, nullable=True)
    evidence_status = Column(String(30), nullable=False, default="unverified")
    visual_brief_json = Column(Text, nullable=True)
    asset_provenance_json = Column(Text, nullable=True)
    media_variant_ids_json = Column(Text, nullable=True)
    visual_qa_status = Column(String(30), nullable=False, default="not_run")
    visual_qa_flags_json = Column(Text, nullable=True)
    status = Column(String(30), nullable=False, default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization")
    source_content = relationship("Content")
    theme = relationship("BrandTheme")
    opportunity = relationship("ContentOpportunity")

    __table_args__ = (
        UniqueConstraint("source_content_id", "platform", name="uq_content_packages_source_platform"),
    )
